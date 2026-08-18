import os 
from dotenv import load_dotenv
load_dotenv()

from langchain_mistralai import ChatMistralAI , MistralAIEmbeddings
from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import List , TypedDict
from langchain_community.vectorstores import Chroma

llm=ChatMistralAI(model="mistral-small-latest")
embedding_model=MistralAIEmbeddings(model="mistral-embed")
vector_store = Chroma(
    persist_directory="./vectorStore/chroma-db",
    embedding_function=embedding_model
)

class PR_State(TypedDict):

    raw_diff: List[dict]
    parsed_data:List[dict]
    file_code:List[dict]
    dependencies:List[dict]

    repo_Context:List[dict]

    code_analysis:dict
    security_analysis:dict
    impact_analysis:dict

    risk_score:int

    final_decision:str
    final_review:dict


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