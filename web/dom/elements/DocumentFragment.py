from web.dom.Document import Document
from web.dom.Node import Node


class DocumentFragment(Node):
    def __init__(self, *args: str, **kwargs: int) -> None:
        super(DocumentFragment, self).__init__(*args, **kwargs)