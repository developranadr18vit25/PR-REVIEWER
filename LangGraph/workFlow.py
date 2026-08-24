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
    repo_path:str
    pr_number:str
    target_branch:str
    file_code:List[dict]
    dependencies:List[dict]

    repo_Context:List[dict]

    code_analysis:dict
    merge_analysis:dict
    isConflict:bool
    conflict_analysis:List[dict]
    security_analysis:dict
    

    risk_score:int

    final_decision:str
    final_review:dict


    
