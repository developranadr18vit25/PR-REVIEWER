from dotenv import load_dotenv
load_dotenv()
from langchain_community.vectorstores import Chroma
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter,Language
import os

embedding_model=MistralAIEmbeddings(model="mistral-embed")

def chunk_data()->list:

    repo_path="../backend/repos"
    chunks=[]
    allowed_extensions=(".html" , ".css" , ".js")

    for root,dirs,files in os.walk(repo_path):

        for file in files:

            if not file.endswith(allowed_extensions):
                continue

            file_path=os.path.join(root,file)

            with open(file_path , "r" , encoding="utf-8") as f:
                code=f.read()

            if file.endswith(".html"):

                splitter=RecursiveCharacterTextSplitter.from_language(

                    language=Language.HTML,
                    chunk_size=1000,
                    chunk_overlap=150
                )

            elif file.endswith(".js"):
                splitter=RecursiveCharacterTextSplitter.from_language(
                    language=Language.JS,
                    chunk_size=1000,
                    chunk_overlap=150
                )
            else:
                splitter=RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=150
                )
            
            chunked_code=splitter.create_documents(
                texts=[code]
            )

            chunks.extend(chunked_code)

    return chunks

chunklist=chunk_data()

def create_db(chunklist):

    vector_db=Chroma.from_documents(
        documents=chunklist,
        embedding=embedding_model,
        persist_directory="chroma-db"
    )


print(chunklist)
create_db(chunklist)
print("Vector db created successfully")