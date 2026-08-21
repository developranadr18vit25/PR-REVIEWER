from pydantic import BaseModel
from workFlow import PR_State
from typing import List , TypedDict
from helper import make_js_tree , find_function_calls , get_language
from workFlow import vector_store

def get_changed_files(state: PR_State):

    file_code = []

    for file in state["parsed_data"]:

        filename = file["filename"]

        docs = vector_store.similarity_search(
            query="",
            k=100,
            filter={
                "file_path": filename
            }
        )

        code = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        file_code.append({
            "filename": filename,
            "code": code
        })

    return {
        "file_code": file_code
    }