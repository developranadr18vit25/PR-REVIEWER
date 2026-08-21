from pydantic import BaseModel
from workFlow import PR_State
from typing import List , TypedDict
from helper import make_js_tree , find_function_calls , get_language
from workFlow import vector_store


def fetch_dependencies(state: PR_State):

    dependencies = []

    for file in state["file_code"]:

        filename = file["filename"]
        code = file["code"]

        language = None

        for parsed_file in state["parsed_data"]:
            if parsed_file["filename"] == filename:
                language = parsed_file["language"]
                break

        if language == "javascript":

            tree = make_js_tree(code)

            calls = find_function_calls(tree.root_node)

            dependencies.append({
                "filename": filename,
                "calls": calls
            })

    return {
        "dependencies": dependencies
    }

def fetch_db_dependencies(state: PR_State):

    file_code = state["file_code"]

    for dependency_info in state["dependencies"]:

        filename = dependency_info["filename"]
        calls = dependency_info["calls"]

        for file in file_code:

            if file["filename"] != filename:
                continue

            dependency_code = []

            for call in calls:

                docs = vector_store.similarity_search(
                    query=call,
                    k=3
                )

                for doc in docs:

                    dependency_code.append({
                        "function": call,
                        "code": doc.page_content,
                        "metadata": doc.metadata
                    })

            file["dependencies"] = dependency_code

    return {
        "file_code": file_code
    }