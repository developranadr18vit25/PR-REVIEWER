from pydantic import BaseModel
from workFlow import PR_State
from typing import List , TypedDict
from helper import make_js_tree , find_function_calls , get_language

def parser_node(state:PR_State)->dict:

    class ChangedFile(BaseModel):

        filename:str
        language:str
        status:str
        additions:int
        deletions:int
        changes:int
        patch:str

    class ParsedPR(BaseModel):

        changed_files: List[ChangedFile]
        

    def parse_pr_diff(raw_diff):

        changed_files = []

        for file in raw_diff["PR_diff"]:

            changed_file = ChangedFile(
                filename=file["filename"],
                language=get_language(file["filename"]),
                status=file["status"],
                additions=file["additions"],
                deletions=file["deletions"],
                changes=file["changes"],
                patch=file["patch"]
            )

            changed_files.append(changed_file)

        return ParsedPR(changed_files=changed_files)

    return {
        "parsed_data":parse_pr_diff(state["raw_diff"])
    }