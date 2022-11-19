from typing import Optional
import requests
from requests.models import Response
import json
from browser.Inspector import NetworkRequest

from browser.globals import BrowserState

def request(url: str, payload: Optional[dict]=None) -> Response:
    inspectors = BrowserState.get_inspectors()
    if url.startswith("http://") or url.startswith("https://"):
        headers = {
                "User-Agent": "theBrowser/0.03-alpha"
            }
        if payload:
            response = requests.post(url, json=json.dumps(payload), headers=headers)
            [inspector.add_network_request(NetworkRequest(url, "POST", response.status_code, len(response.content))) for inspector in inspectors]
        else:
            response = requests.get(url, headers=headers)
            [inspector.add_network_request(NetworkRequest(url, "GET", response.status_code, len(response.content))) for inspector in inspectors]
        return response


def load_file(path: str) -> str:
    path = path.split("file://")[-1]
    contents = ""
    with open(path, "r") as file:
        lines = file.readlines()
        contents = "".join(lines)
    return contents