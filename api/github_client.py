from dotenv import load_dotenv
load_dotenv()
import requests
import os

token=os.getenv("GITHUB_TOKEN")


def get_diff(owner:str ,repo:str , pull_number:str )->list:

    headers={
        "Authorization":f"Bearer {token}"
    }
    response= requests.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files" , headers=headers)
    files=response.json()

    print(files)

    return files


get_diff("developranadr18vit25" , "dhruv1project" , 1)
