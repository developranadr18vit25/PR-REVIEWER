import os

from huggingface_hub import InferenceClient
from workFlow import PR_State
from helper import make_js_tree


MODEL_NAME = "boraoxkan/codereview-ai"

client = InferenceClient(
    api_key=os.environ["HF_TOKEN"]
)

def find_syntax_errors(node):

    errors = []

    if node.type == "ERROR":

        errors.append({
            "start": node.start_point,
            "end": node.end_point
        })

    for child in node.children:

        errors.extend(
            find_syntax_errors(child)
        )

    return errors


def check_syntax(code):

    tree = make_js_tree(code)

    errors = find_syntax_errors(
        tree.root_node
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def check_logic(code, patch, dependencies):

    dependency_text = ""

    for dependency in dependencies:

        dependency_text += f"""
Function:
{dependency["function"]}

Code:
{dependency["code"]}

"""

    prompt = f"""
Analyze this pull request for logical and behavioral bugs.

Focus on bugs introduced by the patch.

Do NOT focus on syntax errors.

Use the full file and dependency code to understand the behavior.

Return:

- Bug found: yes/no
- Severity: low/medium/high
- Location
- Explanation
- Suggested fix

================ PATCH ================

{patch}

================ FULL FILE ================

{code}

================ DEPENDENCIES ================

{dependency_text}

================ RESPONSE ================
"""

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        max_tokens=512,

        temperature=0.1
    )

    return response.choices[0].message.content


def codeAnalysis(state: PR_State):

    filecode = state["file_code"]

    parsed_data = state["parsed_data"]

    syntax_results = []

    logic_results = []

    for file in filecode:

        filename = file["filename"]

        code = file["code"]

        patch = None
        language = None

        for parsed_file in parsed_data:

            if parsed_file["filename"] == filename:

                patch = parsed_file["patch"]

                language = parsed_file["language"]

                break

        dependencies = file.get(
            "dependencies",
            []
        )

        if language == "javascript":

            syntax_result = check_syntax(code)

            syntax_results.append({

                "filename": filename,

                "valid": syntax_result["valid"],

                "errors": syntax_result["errors"]

            })

            if syntax_result["valid"]:

                logic_result = check_logic(
                    code,
                    patch,
                    dependencies
                )

                logic_results.append({

                    "filename": filename,

                    "result": logic_result

                })

            else:

                logic_results.append({

                    "filename": filename,

                    "result":
                        "Logic analysis skipped because syntax errors were found."

                })

        else:

            syntax_results.append({

                "filename": filename,

                "valid": None,

                "errors": [],

                "status": "unsupported_language"

            })

    return {

        "code_analysis": {

            "syntax": syntax_results,

            "logic": logic_results

        }
    }