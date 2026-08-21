from pydantic import BaseModel
from workFlow import PR_State
from typing import List , TypedDict
from helper import make_js_tree , find_function_calls , get_language


def find_syntax_errors(node):

    errors = []

    if node.type == "ERROR":
        errors.append({
            "start": node.start_point,
            "end": node.end_point
        })

    for child in node.children:
        errors.extend(find_syntax_errors(child))

    return errors


def codeanalyssis(state: PR_State):

    filecode = state["file_code"]

    syntax_results = []

    for file in filecode:

        filename = file["filename"]
        code = file["code"]

        language = get_language(filename)

        if language == "javascript":

            tree = make_js_tree(code)

            errors = find_syntax_errors(tree.root_node)

            syntax_results.append({
                "filename": filename,
                "valid": len(errors) == 0,
                "errors": errors
            })

        else:

            syntax_results.append({
                "filename": filename,
                "valid": True,
                "errors": []
            })

    return {
        "code_analysis": {
            "syntax": syntax_results
        }
    }
    