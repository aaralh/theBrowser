from web.dom.elements.DocumentFragment import DocumentFragment
from web.dom.elements.Element import Element

class HTMLTemplateElement(Element):
	def __init__(self, *args, **kwargs):
		super(HTMLTemplateElement, self).__init__(*args, **kwargs)
		self.content: DocumentFragment = DocumentFragment()

	@property
	def content(self) -> DocumentFragment:
		return self.content