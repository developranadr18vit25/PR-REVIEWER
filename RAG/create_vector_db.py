from dotenv import load_dotenv
load_dotenv()
from langchain_community.vectorstores import Chroma
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter,Language
import os


def chunk_data()->list:

    repo_path="repositories/PASSWORD-MANAGER"
    chunks=[]

    for root,dirs,files in os.walk(repo_path):

        for file in files:
            file_path=os.path.join(root,file)

            with open(file_path , "r" , encoding="utf-8") as f:
                code=f.read()

            if file.endswith(".html"):

                splitter=RecursiveCharacterTextSplitter.from_language(
                    Language.HTML,
                    chunk_size=1000,
                    chunk_overlap=150
                )

            elif file.endswith(".js"):
                splitter=RecursiveCharacterTextSplitter.from_language(
                    Language.JS,
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

print(chunklist)