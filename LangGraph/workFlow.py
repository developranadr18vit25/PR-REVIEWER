import os 
from dotenv import load_dotenv
load_dotenv()

from langchain_mistralai import ChatMistralAI , MistralAIEmbeddings
from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import List , TypedDict
from langchain_community.vectorstores import Chroma
from helper import make_js_tree , find_function_calls , get_language

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

    
