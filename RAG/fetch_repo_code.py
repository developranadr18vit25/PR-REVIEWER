from dotenv import load_dotenv
load_dotenv()
from git import Repo
import os

# def fetch_from_github():
#     repo_url="https://github.com/developranadr18vit25/PASSWORD-MANAGER"
#     repo_name="PASSWORD-MANAGER"

#     os.makedirs("repositories" , exist_ok=True)

#     clone_path=os.path.join("repositories" , repo_name)

#     Repo.clone_from(repo_url,clone_path)
#     print("Repository cloned successfully")

# # fetch_from_github()

def convert_to_text()->str:

    code=""
    
    repo_path="../backend/repos"

    print(os.path.abspath(repo_path))

    for root , dirs , files in os.walk(repo_path):

        allowed_extensions=(".html" , ".css" , ".js")

        for file in files:
            if file.endswith(allowed_extensions):
                file_path=os.path.join(root,file)

                with open(file_path , "r" , encoding="utf-8") as f:
                    code+=f.read()

    print(code)
    return code


convert_to_text()





