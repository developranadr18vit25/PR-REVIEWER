import os
import json
import subprocess

from huggingface_hub import InferenceClient

from workFlow import PR_State


MODEL_NAME = "Qwen/Qwen2.5-Coder-32B-Instruct"


client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
    provider="auto"
)


def get_conflict_content(repo_path, filename):

    result = subprocess.run(
        [
            "git",
            "diff",
            "--",
            filename
        ],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to get conflict for {filename}:\n"
            f"{result.stderr}"
        )

    return result.stdout


def get_conflicting_files(state):

    simulated_merge = state["simulated_merge"]

    return simulated_merge.get(
        "conflicting_files",
        []
    )


def get_dependencies_for_file(state, filename):

    for file in state.get("file_code", []):

        if file.get("filename") == filename:

            return file.get(
                "dependencies",
                []
            )

    return []

def get_file_code(state, filename):

    file_code = state.get(
        "file_code",
        []
    )

    for file in file_code:

        if file.get("filename") == filename:

            return file.get(
                "code",
                ""
            )

    return ""


def get_patch(state, filename):

    parsed_data = state.get(
        "parsed_data",
        []
    )

    for file in parsed_data:

        if file.get("filename") == filename:

            return file.get(
                "patch",
                ""
            )

    return ""


def format_dependencies(dependencies):

    if not dependencies:

        return "No dependency information available."

    result = ""

    for dependency in dependencies:

        result += f"""
        
FILE:
{dependency.get("filename", "unknown")}

FUNCTION:
{dependency.get("function", "unknown")}

CODE:
{dependency.get("code", "")}

------------------------------
"""

    return result


def analyze_conflict_with_llm(
    filename,
    conflict,
    file_code,
    patch,
    dependencies,
    repo_context
):

    dependency_text = format_dependencies(
        dependencies
    )

    prompt = f"""
You are an expert software engineer analyzing
a Git merge conflict.

Your job is NOT simply to choose the MAIN version
or the PR version.

You must understand the behavior of both versions
using the repository context and dependencies.

==================================================
CONFLICTING FILE
==================================================

{filename}


==================================================
GIT CONFLICT
==================================================

{conflict}


==================================================
CURRENT FILE CONTEXT
==================================================

{file_code}


==================================================
PR PATCH
==================================================

{patch}


==================================================
DEPENDENCIES
==================================================

{dependency_text}


==================================================
REPOSITORY CONTEXT
==================================================

{repo_context}


==================================================
TASK
==================================================

Analyze this merge conflict.

Answer all of the following:

1. Why did the merge conflict occur?

2. What changes were made in the MAIN branch?

3. What changes were made by the PR?

4. What is the behavioral difference between
   the two versions?

5. What code should be preserved?

6. Should the MAIN version be kept?

7. Should the PR version be kept?

8. Should the two changes be combined?

9. What exact changes should the developer make
   to resolve the conflict?

10. Which files need to be modified?

11. Which functions may be affected?

12. Could resolving the conflict incorrectly
    introduce a bug or break existing behavior?

Do NOT blindly prefer MAIN.

Do NOT blindly prefer the PR.

Use the supplied dependency and repository
context to justify your recommendation.

Return your answer in the following structure:

WHY_CONFLICT:
...

MAIN_BEHAVIOR:
...

PR_BEHAVIOR:
...

BEHAVIORAL_DIFFERENCE:
...

RECOMMENDED_RESOLUTION:
...

REQUIRED_CHANGES:
...

AFFECTED_FILES:
...

AFFECTED_FUNCTIONS:
...

RISKS:
...

CONFIDENCE:
low/medium/high
"""

    response = client.chat_completion(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software engineer "
                    "specializing in Git merge conflicts "
                    "and repository-level code analysis."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        max_tokens=3000
    )

    return response.choices[0].message.content


def conflict_analysis(state: PR_State):

    simulated_merge = state.get(
        "simulated_merge",
        {}
    )

    if not simulated_merge.get(
        "merge_conflict",
        False
    ):

        return {
            "conflict_analysis": {
                "has_conflict": False,
                "results": []
            }
        }

    conflicting_files = get_conflicting_files(
        state
    )

    repo_path = state["repo_path"]

    repo_context = state.get(
        "repo_Context",
        []
    )

    results = []

    for filename in conflicting_files:

        conflict = get_conflict_content(
            repo_path,
            filename
        )

        file_code = get_file_code(
            state,
            filename
        )

        patch = get_patch(
            state,
            filename
        )

        dependencies = get_dependencies_for_file(
            state,
            filename
        )

        analysis = analyze_conflict_with_llm(

            filename=filename,

            conflict=conflict,

            file_code=file_code,

            patch=patch,

            dependencies=dependencies,

            repo_context=repo_context
        )

        results.append({

            "filename": filename,

            "conflict": conflict,

            "analysis": analysis

        })

    return {

        "conflict_analysis": {

            "has_conflict": True,

            "conflicting_files": conflicting_files,

            "results": results

        }
    }