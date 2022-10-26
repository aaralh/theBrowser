from typing import Optional
import requests
from requests.models import Response
import json

def request(url: str, payload: Optional[dict]=None) -> Response:
    if url.startswith("http://") or url.startswith("https://"):
        headers = {
                "User-Agent": "theBrowser/0.03-alpha"
            }
        if payload:
            response = requests.post(url, json=json.dumps(payload), headers=headers)
        else:
            response = requests.get(url, headers=headers)
        return response


def load_file(path: str) -> str:
    path = path.split("file://")[-1]
    contents = ""
    with open(path, "r") as file:
        lines = file.readlines()
        contents = "".join(lines)
    return contents