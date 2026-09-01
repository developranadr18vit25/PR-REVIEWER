from pydantic import BaseModel
from workFlow import PR_State
from typing import List , TypedDict
from helper import make_js_tree , find_function_calls , get_language
from workFlow import vector_store


def fetch_dependencies(state: PR_State):

    for file in state["file_code"]:

        dependencies = []

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
                "calls": calls
            })

        file["dependencies"]=dependencies

    return {
        "file_code":state['file_code']
    }

def fetch_db_dependencies(state: PR_State):

    file_code = state["file_code"]

    for file in state['file_code']:

        code=[]

        for dependency in file["dependencies"]:

            code=[]

            for call in dependency['calls']:

                docs=vector_store.similarity_search(
                    query=call,
                    k=3
                )

                for doc in docs:

                    code.append({
                        "functionName":call,
                        "functionCode":doc.page_content
                    })

            dependency["fetched_code"]=code

    return {
        "file_code": file_code
    }
