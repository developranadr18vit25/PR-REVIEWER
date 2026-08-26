import os
import subprocess

from huggingface_hub import InferenceClient
from workFlow import PR_State


MODEL_NAME = "Qwen/Qwen2.5-Coder-32B-Instruct"


client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
    provider="auto"
)


def get_conflict_content(worktree, filename):

    result = subprocess.run(
        [
            "git",
            "diff",
            "--",
            filename
        ],
        cwd=worktree,
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

    simulated_merge = state.get(
        "simulated_merge",
        {}
    )

    return simulated_merge.get(
        "conflicting_files",
        []
    )


def get_dependencies_for_file(state, filename):

    file_code = state.get(
        "file_code",
        []
    )

    for file in file_code:

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
You are a senior software engineer specializing in
Git merge conflicts and repository-level code analysis.

Analyze the following Git merge conflict.

Do NOT blindly prefer MAIN.
Do NOT blindly prefer the PR.

Understand the behavior of both versions and determine
whether the changes should be kept, rejected, or combined.

==================================================
CONFLICTING FILE
==================================================

{filename}


==================================================
GIT CONFLICT
==================================================

{conflict}


==================================================
FULL FILE CODE
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

Answer:

1. Why did the merge conflict occur?

2. What changes were made in MAIN?

3. What changes were made by the PR?

4. What is the behavioral difference between them?

5. Should MAIN be preserved?

6. Should the PR be preserved?

7. Should both changes be combined?

8. What exact code changes should the developer make?

9. Which files need to be modified?

10. Which functions are affected?

11. What bugs could occur if the conflict is resolved incorrectly?

12. How confident are you in the recommendation?

Return the result using this structure:

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
                    "specializing in Git merge conflicts, "
                    "code review, and repository-level "
                    "software analysis."
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
                "conflicting_files": [],
                "results": []
            }
        }


    worktree = simulated_merge.get(
        "worktree"
    )

    if not worktree:

        return {
            "conflict_analysis": {
                "has_conflict": True,
                "conflicting_files": [],
                "results": [],
                "error": (
                    "Merge conflict was detected, "
                    "but the temporary worktree path "
                    "was not found."
                )
            }
        }


    conflicting_files = get_conflicting_files(
        state
    )


    repo_context = state.get(
        "repo_Context",
        []
    )


    results = []


    for filename in conflicting_files:


        conflict = get_conflict_content(
            worktree,
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