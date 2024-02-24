from web.dom.elements.DocumentFragment import DocumentFragment
from web.dom.elements.Element import Element


class HTMLTemplateElement(Element):
    def __init__(self, *args: str, **kwargs: int) -> None:
        super(HTMLTemplateElement, self).__init__(*args, **kwargs)
        self.__content: DocumentFragment = DocumentFragment(*args[1:])

        #TODO: Handle template element flow correctly.
        # This is just hacky way to make sure that the element is not displayed unless told so by other css rule or etc.
        if self.style is None:
            self.style = {}
        self.style["display"] = "none"

    @property
    def content(self) -> DocumentFragment:
        return self.__content
