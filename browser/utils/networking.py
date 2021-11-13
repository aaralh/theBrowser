import requests
from requests.models import Response
import json

def request(url: str, payload=None) -> Response:
    headers = {
            "User-Agent": "theBrowser/0.03-alpha"
        }
    if payload:
        response = requests.post(url, json=json.dumps(payload), headers=headers)
    else:
        response = requests.get(url, headers=headers)
    return response