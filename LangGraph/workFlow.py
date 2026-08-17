import os 
from dotenv import load_dotenv
load_dotenv()

from langchain_mistralai import ChatMistralAI
from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import List , TypedDict

llm=ChatMistralAI(model="mistral-small-latest")


class PR_State(TypedDict):

    raw_diff: dict
    parsed_data:dict
    related_code:list

    code_analysis:dict
    security_analysis:dict
    impact_analysis:dict

    risk_score:int

    final_decision:str
    final_review:dict



def parser_node(state:PR_State)->dict:

    class ChangedFile(BaseModel):

        filename:str
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