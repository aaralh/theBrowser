from typing import Dict, Optional
import requests
from requests.models import Response
import json
from browser.Inspector import NetworkRequest
from charset_normalizer import detect
from urllib.parse import urlparse
from browser.globals import BrowserState

REQUEST_CACHE: Dict[str, Response] = {}

def parse_host(url: str) -> str:
    parsed_uri = urlparse(url)
    return '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

def resolve_url(url: str, current: str) -> str:
    if "://" in url:
        return url
    elif url.startswith("//"):
        return "https:" + url
    elif url.startswith("/"):
        host = parse_host(current)
        if host.endswith("/"):
            return host[:-1] + url
        return host + url
    elif not url.startswith("/") and not current.endswith("/"):
        host = parse_host(current)
        return host + "/" + url
    else:
        dir, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if dir.count("/") == 2: continue
            dir, _ = dir.rsplit("/", 1)
        return dir + "/" + url

def request(url: str, payload: Optional[dict]=None) -> Response:
    inspectors = BrowserState.get_inspectors()
    if url.startswith("http://") or url.startswith("https://"):
        if REQUEST_CACHE.get(url) and not payload:
            return REQUEST_CACHE.get(url)
        headers = {
                "User-Agent": "theBrowser/0.4-alpha"
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
