from typing import Dict, Optional
import requests
from requests.models import Response
import json
from browser.Inspector import NetworkRequest
from charset_normalizer import detect

from browser.globals import BrowserState

REQUEST_CACHE: Dict[str, Response] = {}


def request(url: str, payload: Optional[dict]=None) -> Response:
    inspectors = BrowserState.get_inspectors()
    if url.startswith("http://") or url.startswith("https://"):
        if REQUEST_CACHE.get(url) and not payload:
            return REQUEST_CACHE.get(url)
        headers = {
                "User-Agent": "theBrowser/0.03-alpha"
            }
        if payload:
            response = requests.post(url, json=json.dumps(payload), headers=headers)
            response.encoding = "UTF-8"
            [inspector.add_network_request(NetworkRequest(url, "POST", response.status_code, len(response.content))) for inspector in inspectors]
        else:
            response = requests.get(url, headers=headers)
            response.encoding = "UTF-8"
            [inspector.add_network_request(NetworkRequest(url, "GET", response.status_code, len(response.content))) for inspector in inspectors]
        if not payload:
            REQUEST_CACHE[url] = response
        return response


def load_file(path: str) -> str:
    path = path.split("file://")[-1]
    contents = ""
    encoding = detect(open(path, "rb").read())["encoding"]
    with open(path, "r", encoding=encoding) as file:
        lines = file.readlines()
        contents = "".join(lines)
    return contents
