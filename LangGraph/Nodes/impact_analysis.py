import os
import json

from huggingface_hub import InferenceClient
from workFlow import PR_State


MODEL_NAME = "boraoxkan/codereview-ai"

client = InferenceClient(
    api_key=os.environ["HF_TOKEN"]
)


def get_logic_errors(state):

    code_analysis = state.get(
        "code_analysis",
        {}
    )

    logic_results = code_analysis.get(
        "logic",
        []
    )

    errors = []

    for result in logic_results:

        analysis = result.get(
            "result",
            ""
        )

        errors.append({
            "filename": result.get(
                "filename",
                "unknown"
            ),
            "analysis": analysis
        })

    return errors


def get_related_functions(state, filename):

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


def get_dependencies(state, filename):

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


# ============================================================


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

----------------------------------------
"""

    return result




def analyze_impact_with_llm(
    filename,
    logic_error,
    file_code,
    dependencies
):

    dependency_text = format_dependencies(
        dependencies
    )

    prompt = f"""
You are a senior software engineer performing
repository-level impact analysis.

A previous code analysis detected a logical or
behavioral bug in a pull request.

Your job is NOT to find a new bug.

Your job is to determine how the identified bug
can propagate through the rest of the application.

You must analyze:

1. The function containing the bug.
2. Other functions that depend on it.
3. Data returned by the affected function.
4. How that data is used by other functions.
5. Which files may be affected.
6. Which application behavior may change.
7. Whether the bug can propagate further.

Do NOT assume that every dependency is affected.

Only mark a function or file as affected if there
is a reasonable data-flow or behavioral relationship.

==================================================
FILE CONTAINING LOGICAL BUG
==================================================

{filename}


==================================================
LOGIC ANALYSIS RESULT
==================================================

{logic_error}


==================================================
FULL FILE CODE
==================================================

{file_code}


==================================================
RELATED FUNCTIONS / DEPENDENCIES
==================================================

{dependency_text}


==================================================
TASK
==================================================

Trace the potential impact of this logical bug.

Determine:

1. What function contains the original problem?

2. What data or behavior produced by that function
   can be incorrect?

3. Which other functions consume that data or
   depend on that behavior?

4. Which other files may be affected?

5. What data may become incorrect?

6. What application behavior may break?

7. How far can the bug propagate?

8. Are there functions that are NOT affected?

9. What should the developer test after fixing
   the original bug?

Return ONLY this structure:

ORIGINAL_BUG:
...

ORIGINAL_FUNCTION:
...

INCORRECT_DATA_OR_BEHAVIOR:
...

AFFECTED_FUNCTIONS:
- file: ...
  function: ...
  reason: ...

AFFECTED_FILES:
- file: ...
  reason: ...

AFFECTED_DATA:
- data: ...
  impact: ...

DOWNSTREAM_IMPACT:
...

PROPAGATION_PATH:
...

UNAFFECTED_COMPONENTS:
...

RECOMMENDED_TESTS:
...

IMPACT_SEVERITY:
LOW/MEDIUM/HIGH/CRITICAL

CONFIDENCE:
low/medium/high
"""

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software engineer "
                    "specializing in dependency analysis, "
                    "data flow, and software impact analysis."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        max_tokens=2500,

        temperature=0.1
    )

    return response.choices[0].message.content


def impact_analysis(state: PR_State):


    logic_errors = get_logic_errors(state)

    if not logic_errors:

        return {
            "impact_analysis": {
                "success": True,
                "has_logical_errors": False,
                "results": []
            }
        }


    impact_results = []




    for error in logic_errors:

        filename = error.get(
            "filename"
        )

        logic_error = error.get(
            "analysis",
            ""
        )


        # ----------------------------------------------------
        # Get complete file containing the bug
        # ----------------------------------------------------

        file_code = get_file_code(
            state,
            filename
        )


    

        dependencies = get_dependencies(
            state,
            filename
        )



        impact = analyze_impact_with_llm(

            filename=filename,

            logic_error=logic_error,

            file_code=file_code,

            dependencies=dependencies
        )


        impact_results.append({

            "filename": filename,

            "logic_error": logic_error,

            "impact": impact

        })


    return {

        "impact_analysis": {

            "success": True,

            "has_logical_errors": True,

            "issue_count": len(logic_errors),

            "results": impact_results

        }

    }