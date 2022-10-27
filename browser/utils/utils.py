from typing import List
from urllib.parse import urlparse
from web.dom.Node import Node


def tree_to_list(node: Node, list: List) -> List[Node]:
    list.append(node)
    for child in node.children:
        tree_to_list(child, list)
    return list

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
        return host + url
    else:
        dir, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if dir.count("/") == 2: continue
            dir, _ = dir.rsplit("/", 1)
        return dir + "/" + url
