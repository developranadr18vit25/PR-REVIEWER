import os
import subprocess
import json

from huggingface_hub import InferenceClient
from workFlow import PR_State


MODEL_NAME = "Qwen/Qwen2.5-Coder-32B-Instruct"


client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
    provider="auto"
)

def run_semgrep(worktree):

    result = subprocess.run(
        [
            "semgrep",
            "--config=auto",
            "--json",
            worktree
        ],
        capture_output=True,
        text=True
    )

    try:

        return json.loads(result.stdout)

    except json.JSONDecodeError:

        raise RuntimeError(
            "Could not parse Semgrep output.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

def get_finding_code(worktree, finding):

    filename = finding.get("path")

    start_line = finding.get(
        "start",
        {}
    ).get(
        "line",
        1
    )

    end_line = finding.get(
        "end",
        {}
    ).get(
        "line",
        start_line
    )

    file_path = os.path.join(
        worktree,
        filename
    )

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            lines = file.readlines()

        context_start = max(
            0,
            start_line - 6
        )

        context_end = min(
            len(lines),
            end_line + 5
        )

        return "".join(
            lines[
                context_start:context_end
            ]
        )

    except Exception:

        return ""

def analyze_security_finding(
    finding,
    code
):

    prompt = f"""
You are a senior application security engineer.

Semgrep has detected a potential security issue
in a software repository.

Your job is to analyze the Semgrep finding and
determine what the actual security problem is.

Do NOT blindly trust the Semgrep finding.

Determine whether the finding is:

- a real vulnerability
- a false positive
- a potential vulnerability requiring review

==================================================
SEMGREP FINDING
==================================================

{json.dumps(finding, indent=2)}

==================================================
RELEVANT CODE
==================================================

{code}

==================================================
TASK
==================================================

Analyze this security finding.

Explain:

1. What security issue was detected?

2. Is this a real vulnerability or a false positive?

3. Why is the code vulnerable?

4. What is the potential attack scenario?

5. What input or data could an attacker control?

6. What security impact could occur?

7. What exact code or logic should be changed?

8. Which file is affected?

9. Which function or code section is affected?

10. How severe is the vulnerability?

Use the following severity levels:

CRITICAL
HIGH
MEDIUM
LOW
INFO

Return ONLY the following structure:

SECURITY_ISSUE:
...

IS_VULNERABLE:
true/false/uncertain

VULNERABILITY_TYPE:
...

WHY_VULNERABLE:
...

ATTACK_SCENARIO:
...

ATTACKER_CONTROLLED_INPUT:
...

SECURITY_IMPACT:
...

RECOMMENDED_FIX:
...

AFFECTED_FILE:
...

AFFECTED_FUNCTION:
...

SEVERITY:
CRITICAL/HIGH/MEDIUM/LOW/INFO

CONFIDENCE:
low/medium/high
"""

    response = client.chat_completion(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior application security "
                    "engineer specializing in vulnerability "
                    "analysis and secure code review."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        max_tokens=2000
    )

    return response.choices[0].message.content


def security_analysis(state: PR_State):

    simulated_merge = state.get(
        "simulated_merge"
    )

    if not simulated_merge:

        return {
            "security_analysis": {
                "success": False,
                "error": (
                    "Simulated merge has not been performed."
                )
            }
        }

    if simulated_merge.get(
        "merge_conflict",
        False
    ):

        return {
            "security_analysis": {
                "success": False,
                "skipped": True,
                "reason": (
                    "Merge conflict detected. "
                    "Security scan skipped."
                )
            }
        }

    worktree = simulated_merge.get(
        "worktree"
    )

    if not worktree:

        return {
            "security_analysis": {
                "success": False,
                "error": (
                    "Merged worktree path was not found."
                )
            }
        }

    try:


        semgrep_output = run_semgrep(
            worktree
        )

        findings = semgrep_output.get(
            "results",
            []
        )

        analyzed_findings = []

        for finding in findings:

            code = get_finding_code(
                worktree,
                finding
            )

            llm_analysis = analyze_security_finding(
                finding=finding,
                code=code
            )

            analyzed_findings.append({

                "semgrep_finding": finding,

                "code": code,

                "llm_analysis": llm_analysis

            })

        return {

            "security_analysis": {

                "success": True,

                "finding_count": len(findings),

                "semgrep_findings": findings,

                "analyzed_findings": analyzed_findings,

                "errors": semgrep_output.get(
                    "errors",
                    []
                )

            }

        }

    except Exception as e:

        return {

            "security_analysis": {

                "success": False,

                "error": str(e)

            }
        }