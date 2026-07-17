from dotenv import load_dotenv
load_dotenv()

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel

import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from api.github_client import get_diff


class Issue(BaseModel):
    category:str
    severity:str
    title:str
    explanation:str
    confidence:float

class Summary(BaseModel):
    overall_score:int

class Review(BaseModel):
    summary:Summary
    issues:Issue


prompt=ChatPromptTemplate.from_messages([
    ("system","You are an GITHUB Pull Requests reviewer. From the given context which are the differences , you have to analyze and tell whether it is safe to merge the file or not . If not point out the error and suggest what to change"),

    ("human","{context}")
])

model=ChatMistralAI(model="mistral-small-latest")


response=prompt | model | StrOutputParser()

final_review=Review.model_validate_json(response.invoke(get_diff("developranadr18vit25" , "dhruv1project" , 1)))

print(final_review)








