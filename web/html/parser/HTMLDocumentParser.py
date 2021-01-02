from enum import Enum, Flag, auto
from os import name
from typing import Any, List, Union, Callable, cast
from web.dom.elements.HTMLScriptElement import HTMLScriptElement
from web.dom.elements.HTMLTemplateElement import HTMLTemplateElement
from web.html.parser.ListOfActiveElements import ListOfActiveElements
from web.html.parser.StackOfOpenElments import StackOfOpenElments
from web.dom.CharacterData import CharacterData
from web.dom.elements.Comment import Comment
from web.html.parser.utils import charIsWhitespace
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.Node import Node
from web.dom.elements.Text import Text
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from web.html.parser.HTMLTokenizer import HTMLTokenizer
from web.dom.ElementFactory import ElementFactory
from dataclasses import dataclass
from copy import deepcopy

class HTMLDocumentParser:

	@dataclass
	class AdjustedInsertionLocation:
		parent: Union[Element, None] = None
		insertBeforeSibling: Union[Element, None] = None # If none insert as last child.


	class __Mode(Enum):
		Initial = auto()
		BeforeHTML = auto()
		BeforeHead = auto()
		InHead = auto()
		InHeadNoscript = auto()
		AfterHead = auto()
		InBody = auto()
		Text = auto()
		InTable = auto()
		InTableText = auto()
		InCaption = auto()
		InColumnGroup = auto()
		InTableBody = auto()
		InRow = auto()
		InCell = auto()
		InSelect = auto()
		InSelectInTable = auto()
		InTemplate = auto()
		AfterBody = auto()
		InFrameset = auto()
		AfterFrameset = auto()
		AfterAfterBody = auto()
		AfterAfterFrameset = auto()

	def __init__(self, html: str) -> None:
		self.__currentInsertionMode = self.__Mode.Initial
		self.__originalInsertionMode: Union[self.__Mode, None] = None
		self.__openElements = StackOfOpenElments()
		self.__tokenizer = HTMLTokenizer(html, self.__tokenHandler)
		self.__document = Document()
		self.__documentNode = None
		self.__scripting: bool = False
		self.__framesetOK: bool = True
		self.__formattingElements = ListOfActiveElements()
		self.__fosterParenting: bool = False
		self.parsingFragment: bool = False
		self.invokefWhileDocumentWrite: bool = False
		self.__formElement: Union[Element, None] = None

	@property
	def __currentElement(self) -> Node:
		'''
		Gets the latest opened element aka "parent".
		'''
		return self.__documentNode if self.__openElements.isEmpty() else self.__openElements.last() 


	def run(self) -> None:
		self.__tokenizer.run()

	def __tokenHandler(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
		
		print("Token: ", token)
		print("Input mode: ", self.__currentInsertionMode)

		switcher = self.__getModeSwitcher()
		if (switcher != None):
			switcher(token)

		if (token.type == HTMLToken.TokenType.EOF):
			print("The dom")
			print(self.__documentNode)

	def __continueIn(self, mode: __Mode) -> None:
		self.__switchModeTo(mode)

	def __switchModeTo(self, newMode: __Mode) -> None:
		'''
		Switch state and consume next character.
		'''
		self.__currentInsertionMode = newMode

	def __reconsumeIn(self, newMode: __Mode, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
		'''
		Switch state without consuming next character.
		'''
		self.__currentInsertionMode = newMode
		switcher = self.__getModeSwitcher()
		if (switcher != None):
			switcher(token)

	def __createElement(self, token: HTMLTag) -> Element:
		'''
		Creates element based on given token and sets parent for it.
		'''
		parent = self.__currentElement
		element = ElementFactory.create_element(token, parent, self.__document)
		element.parentNode.appendChild(element)

		return element

	def __createElementWihtAdjustedLocation(self, token: HTMLTag, adjustedLocation: AdjustedInsertionLocation):
		'''
		Creates element based on given token and inserts it based on adjsuted location.
		'''
		parent = adjustedLocation.parent
		element = ElementFactory.create_element(token, parent, self.__document)
		if (adjustedLocation.insertBeforeSibling == None):
			element.parentNode.appendChild(element)
		else:
			element.parentNode.appendChildBeforeElement(adjustedLocation.insertBeforeSibling)

		return element

	def __insertCharacter(self, token: HTMLCommentOrCharacter) -> None:
		if (type(self.__currentElement) is Document):
			return
		elif (len(self.__currentElement.childNodes) > 0 and type(self.__currentElement.childNodes[-1]) is Text):
			cast(Text, self.__currentElement.childNodes[-1]).appendData(token.data)
		else:
			textNode = Text(self.__document, self.__currentElement, token.data)
			textNode.parentNode = self.__currentElement
			self.__currentElement.appendChild(textNode)

	def __insertComment(self, token: HTMLCommentOrCharacter) -> None:
		comment = Comment(token.data)
		comment.parentNode = self.__currentElement
		self.__currentElement.appendChild(comment)
		self.__continueIn(self.__Mode.BeforeHead)

	def __adoptionAgencyAlgorithm(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
		subject = token.name
		if (self.__currentElement.name == subject and not self.__formattingElements.contains(self.__currentElement)):
			self.__openElements.pop()
			return
		outerLoopCounter = 0

		while outerLoopCounter < 8:
			outerLoopCounter += 1
			formattingElementResult = self.__formattingElements.lastElementWithTagNameBeforeMarker(subject)
			formattingElement = formattingElementResult.element
			if (formattingElement is None):
				return

			if (not self.__openElements.containsElement(formattingElement)):
				self.__formattingElements.remove(formattingElement)
				return
			if(self.__openElements.containsElement(formattingElement) and not self.__openElements.hasInScope()):
				return
			if (formattingElement != self.__currentElement):
				#TODO: Handle parsing error.
				pass
			
			furtherMostBlock = self.__openElements.topmostSpecialNodeBelow(formattingElement)

			if (furtherMostBlock is None):
				self.__openElements.popUntilElementWithAtagNameHasBeenPopped(formattingElement.name)
				self.__formattingElements.remove(formattingElement)
				return

			""" commonAncestor = self.__openElements.elementBefore(formattingElement)
			bookMark = formattingElementResult.index

			node = deepcopy(furtherMostBlock.element)
			lastNode = deepcopy(furtherMostBlock.element)
			innerLoopCounter = 0
			while (innerLoopCounter <= 3):
				node = self.__openElements.elementBefore(node)
				if (node is None):
					node = self.__openElements.getElementOnIndex(fur) """

			# bookmark = 
			# case 13
			# TODO: Continue here https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm
			# https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-scope

	def __generateImpliedEndTags(self, exception: str) -> None:
		while (self.__currentElement.name is not exception and  self.__currentElement.name in ["caption", "colgroup", "dd", "dt", "li", "optgroup", "option", "p", "rb", "rp", "rt", "rtc", "tbody", "td", "tfoot", "th", "thead", "tr"]):
			self.__openElements.pop()

	def __findAppropriatePlaceForInsertingNode(self) -> AdjustedInsertionLocation:
		target = self.__currentElement
		adjustedLocation = self.AdjustedInsertionLocation()

		if (self.__fosterParenting and target.name in ["table", "tbody", "tfoot", "thead", "tr"]):
			templateResult = self.__openElements.lastElementWithTagName("template")
			tableResult = self.__openElements.lastElementWithTagName("table")
			if (templateResult != None and tableResult == None or (tableResult != None and tableResult.index < templateResult.index)):
					adjustedLocation.parent = templateResult.element
					adjustedLocation.insertBeforeSibling = None
					return adjustedLocation
			elif (tableResult == None):
				adjustedLocation.parent = self.__openElements.first()
				adjustedLocation.insertBeforeSibling = None
				return adjustedLocation
			elif (tableResult != None and tableResult.element.parentNode != None):
				adjustedLocation.parent = tableResult.element.parentNode
				adjustedLocation.insertBeforeSibling = tableResult.element
				return adjustedLocation
			
			previousElement = self.__openElements.elementBefore(tableResult.element)
			adjustedLocation.parent = previousElement
			adjustedLocation.insertBeforeSibling = None
			return adjustedLocation
		else:
			adjustedLocation.parent = target
			adjustedLocation.insertBeforeSibling = None
		
		if (adjustedLocation.parent.name == "template"):
			adjustedLocation.parent = cast(HTMLTemplateElement, adjustedLocation.parent).content
			adjustedLocation.insertBeforeSibling = None

		return adjustedLocation

	def __getModeSwitcher(self) -> Union[Callable[[], None], None]:

		def handleInitial(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.DOCTYPE):
				token = cast(HTMLDoctype, token)
				documentNode = DocumentType(token, self.__document)
				self.__documentNode = documentNode
				# TODO: Handle quircks mode.
				self.__switchModeTo(self.__Mode.BeforeHTML)

		def handleBeforeHTML(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.StartTag):
				token = cast(HTMLTag, token)
				if (token.name == "html"):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__switchModeTo(self.__Mode.BeforeHead)
				else:
					token = HTMLTag(HTMLToken.TokenType.StartTag)
					token.name = "html"
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__switchModeTo(self.__Mode.BeforeHead)

		def handleBeforeHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.Character):
				if (charIsWhitespace(token.data)):
					self.__continueIn(self.__Mode.BeforeHead)
			elif (token.type == HTMLToken.TokenType.Comment):
				self.__insertComment(token)
			elif (token.type == HTMLToken.TokenType.DOCTYPE):
				self.__continueIn(self.__Mode.BeforeHead)
			elif (token.type == HTMLToken.TokenType.StartTag):
				token = cast(HTMLTag, token)
				if (token.name == "head"):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__switchModeTo(self.__Mode.InHead)
			else:
				token = HTMLTag(HTMLToken.TokenType.StartTag)
				token.name = "head"
				element = self.__createElement(token)
				self.__openElements.push(element)
				self.__switchModeTo(self.__Mode.InHead)

		def handleInHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.Character):
				if (charIsWhitespace(token.data)):
					self.__insertCharacter(token)
			elif (token.type == HTMLToken.TokenType.Comment):
				token = cast(HTMLCommentOrCharacter, token)
				comment = Comment(token.data)
				self.__currentElement.appendChild(comment)
			elif (token.type == HTMLToken.TokenType.DOCTYPE):
				pass
			elif (token.type == HTMLToken.TokenType.StartTag):
				token = cast(HTMLTag, token)
				if (token.name == "html"):
					# TODO: Handle using the "in body"
					raise NotImplementedError
				elif (token.name in ["base", "basefont", "bgsound", "link"]):
					# This kind of elements are not added to open stack.
					_ = self.__createElement(token)
				elif (token.name == "meta"):
					# This kind of elements are not added to open stack.
					element = self.__createElement(token)
					if ("charset" in element.attributes):
						# TODO: Handle charset attribute.
						pass
						
				elif (token.name == "title"):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(
						self.__tokenizer.State.RCDATA)
					print("Assigning insertion mode:", self.__currentInsertionMode)
					self.__originalInsertionMode = self.__currentInsertionMode
					self.__switchModeTo(self.__Mode.Text)
				elif ((token.name == "noscript" and self.__scripting) or (token.name in ["noframes", "style"])):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(
						self.__tokenizer.State.RAWTEXT)
					self.__originalInsertionMode = self.__currentInsertionMode
					self.__switchModeTo(self.__Mode.Text)
				elif (token.name == "noscript" and not self.__scripting):
					_ = self.__createElement(token)
					self.__switchModeTo(self.__Mode.InHeadNoscript)
				elif (token.name == "script"):
					# TODO: Add support for JS.
					adjustedInsertionLocation = self.__findAppropriatePlaceForInsertingNode()
					element = cast(HTMLScriptElement, self.__createElementWihtAdjustedLocation(token, adjustedInsertionLocation))
					element.parserDocument = self.__document
					element.isNonBlocking = False

					if (self.parsingFragment):
						raise NotImplementedError
					if (self.invokefWhileDocumentWrite):
						raise NotImplementedError

					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(self.__tokenizer.State.ScriptData)
					self.__originalInsertionMode = self.__currentInsertionMode
					self.__switchModeTo(self.__Mode.Text)
					
				elif (token.name == "template"):
					# TODO: Handle case.
					raise NotImplementedError
				else:
					# Ignores "head" and any other tag.
					pass

			elif (token.type == HTMLToken.TokenType.EndTag):
				if (token.name == "head"):
					self.__openElements.pop()
					self.__switchModeTo(self.__Mode.AfterHead)
				elif (token.name in ["body", "html", "br"]):
					self.__openElements.pop()
					self.__reconsumeIn(self.__Mode.AfterHead, token)
				elif (token.name == "template"):
					# TODO: Handle case.
					raise NotImplementedError
			else:
				self.__openElements.pop()
				self.__reconsumeIn(self.__Mode.AfterHead, token)

		def handleInHeadNoscript(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.DOCTYPE):
				pass
			elif (token.type == HTMLToken.TokenType.StartTag):
				token = cast(HTMLTag, token)
				if (token.name == "html"):
					# TODO: Handle using the "in body".
					raise NotImplementedError
			elif (token.type == HTMLToken.TokenType.EndTag):
				token = cast(HTMLTag, token)
				if (token.name == "noscript"):
					self.__openElements.pop()
					self.__switchModeTo(self.__Mode.InHead)
				elif (token.name == "br"):
					self.__openElements.pop()
				else:
					pass
			elif (token.type == HTMLToken.TokenType.Character):
				if (charIsWhitespace(token.data)):
					# TODO:Insert the character
					raise NotImplementedError
			elif (token.type == HTMLToken.TokenType.Comment):
				token = cast(HTMLCommentOrCharacter, token)
				comment = Comment(token.data)
				self.__currentElement.appendChild(comment)
			elif (token.type == HTMLToken.TokenType.StartTag):
				if (token.name in ["basefont", "bgsound", "link", "meta", "noframes", "style"]):
					# TODO: Implement handling.
					raise NotImplementedError
				elif (token.name in ["head", "noscrip"]):
					pass
			else:
				self.__openElements.pop()

		def handleAfterHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.Character):
				if (charIsWhitespace(token.data)):
					self.__insertCharacter(token)
			elif (token.type == HTMLToken.TokenType.Comment):
				self.__insertComment(token)
			elif (token.type == HTMLToken.TokenType.DOCTYPE):
				pass  # Ignore token
			elif (token.type == HTMLToken.TokenType.StartTag):
				token = cast(HTMLTag, token)
				if (token.name == "html"):
					# TODO: Handle using the "in body".
					raise NotImplementedError
				elif (token.name == "body"):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__switchModeTo(self.__Mode.InBody)
				elif (token.name == "frameset"):
					raise NotImplementedError  # TODO: Handle case.
				elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style", "template", "title"]):
					raise NotImplementedError  # TODO: Handle case.
				elif (token.name == "head"):
					pass  # Ignroe token.
			elif (token.type == HTMLToken.TokenType.EndTag):
				if (token.name == "template"):
					# TODO: Handle case, Process the token using the rules for the "in head" insertion mode.
					raise NotImplementedError
				elif (token.name in ["body", "html", "br"]):
					_token = HTMLTag(HTMLToken.TokenType.StartTag)
					_token.name = "body"
					element = self.__createElement(_token)
					self.__openElements.push(element)
					self.__framesetOK = False
					self.__reconsumeIn(self.__Mode.InBody, token)
				else:
					pass  # Ignore token.
			else:
				_token = HTMLTag(HTMLToken.TokenType.StartTag)
				_token.name = "body"
				element = self.__createElement(_token)
				self.__openElements.push(element)
				self.__reconsumeIn(self.__Mode.InBody, token)

		def handleInBody(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.Character):
				if (token.data is None):
					pass  # Ignore token.
				elif (charIsWhitespace(token.data)):
					# TODO: Reconstruct the active formatting elements, if any.
					self.__insertCharacter(token)
				else:
					# TODO: Reconstruct the active formatting elements, if any.
					self.__insertCharacter(token)
					self.__framesetOK = False
			elif (token.type == HTMLToken.TokenType.Comment):
				self.__insertComment(token)
			elif (token.type == HTMLToken.TokenType.DOCTYPE):
				pass  # Ignore token.
			elif (token.type == HTMLToken.TokenType.StartTag):
				if (token.name == "html"):
					raise NotImplementedError  # Handle case
				elif (token.name == "template"):
					# Handle case, Process the token using the rules for the "in head" insertion mode.
					raise NotImplementedError
				elif (token.name in ["noframes", "style"]):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(
						self.__tokenizer.State.RAWTEXT)
					self.__originalInsertionMode = self.__currentInsertionMode
					self.__switchModeTo(self.__Mode.Text)
				elif (token.name in ["base", "basefont", "bgsound", "link"]):
					# This kind of elements are not added to open stack.
					_ = self.__createElement(token)
				elif (token.name == "meta"):
					# This kind of elements are not added to open stack.
					element = self.__createElement(token)
					if ("charset" in element.attributes):
						# TODO: Handle charset attribute.
						pass
				elif (token.name == "title"):
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(
						self.__tokenizer.State.RCDATA)
					self.__originalInsertionMode = self.__currentInsertionMode
					self.__switchModeTo(self.__Mode.Text)
				elif (token.name == "script"):
					# TODO: Add support for JS.
					adjustedInsertionLocation = self.__findAppropriatePlaceForInsertingNode()
					element = cast(HTMLScriptElement, self.__createElementWihtAdjustedLocation(token, adjustedInsertionLocation))
					element.parserDocument = self.__document
					element.isNonBlocking = False

					if (self.parsingFragment):
						raise NotImplementedError
					if (self.invokefWhileDocumentWrite):
						raise NotImplementedError

					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(self.__tokenizer.State.ScriptData)
					self.__originalInsertionMode = self.__currentInsertionMode
					self.__switchModeTo(self.__Mode.Text)
				elif (token.name == "body"):
					#TODO: handle parse error.
					pass
				elif (token.name == "frameset"):
					raise NotImplementedError  # Handle case
				elif (token.name in ["address", "article", "aside", "blockquote", "center", "details", "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "main", "menu", "nav", "ol", "p", "section", "summary", "ul"]):
					if (self.__openElements.hasInButtonScope("p")):
						self.__openElements.pop()
					element = self.__createElement(token)
					self.__openElements.push(element)
				elif (token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
					if (self.__openElements.hasInButtonScope("p")):
						self.__openElements.pop()
					elif (self.__currentElement.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
						self.__openElements.pop()
					element = self.__createElement(token)
					self.__openElements.push(element)
				elif (token.name in ["pre", "listing"]):
					raise NotImplementedError  # TODO: Handle case
				elif (token.name == "form"):
					if (self.__formElement is not None and self.__openElements.contains("template") is False):
						#TODO: Handle parse error.
						pass
					elif (self.__openElements.hasInButtonScope("p")):
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped("p")
					
					element = self.__createElement(token)
					self.__openElements.push(element)
					
					if (self.__openElements.contains("template") is False):
						self.__formElement = element
				elif (token.name == "li"):
					self.__framesetOK = False
					element = self.__createElement(token)
					self.__openElements.push(element)
					if (self.__currentElement.name == "li"):
						pass
					# TODO: Implement rest of the case
					raise NotImplementedError
				elif (token.name in ["dd", "dt"]):
					self.__framesetOK = False
					element = self.__createElement(token)
					self.__openElements.push(element)
					# TODO: Handle case
					raise NotImplementedError
				elif (token.name == "plaintext"):
					if (self.__openElements.hasInButtonScope("p")):
						self.__openElements.pop()
					element = self.__createElement(token)
					self.__openElements.push(element)
					self.__tokenizer.switchStateTo(
						self.__tokenizer.State.PLAINTEXT)
				elif (token.name == "button"):
					if (self.__openElements.hasInScope(token.name)):
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
					# TODO: Reconstruct the active formatting elements, if any.
					self.__framesetOK = False
					element = self.__createElement(token)
					self.__openElements.push(element)
				elif (token.name == "a"):
					if (self.__openElements.hasInScope(token.name)):
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)

					element = self.__createElement(token)
					self.__openElements.push(element)
				elif (token.name in ["b", "big", "code", "em", "font", "i", "s", "small", "strike", "strong", "tt", "u"]):
					# TODO: Reconstruct the active formatting elements, if any and add handling to all tother places too
					element = self.__createElement(token)
					self.__openElements.push(element)
				elif (token.name == "nobr"):
					if (self.__openElements.hasInScope(token.name)):
						# TODO: run the adoption agency algorithm for the token
						raise NotImplementedError
					self.__createElement(token)
					# TODO: Push onto the list of active formatting elements that element. Add this handling to other places too.

			elif (token.type == HTMLToken.TokenType.EndTag):
				if (token.name == "template"):
					# Handle case, Process the token using the rules for the "in head" insertion mode.
					raise NotImplementedError
				elif (token.name == "body"):
					openBodyElement = self.__openElements.lastElementWithTagName(token.name)
					if (openBodyElement == None):
						pass  # Ignore token.
						# TODO: handle the else case.
					else:
						self.__switchModeTo(self.__Mode.AfterBody)
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
						# TODO: Implement the popping functionality.
				elif (token.name == "html"):
					self.__reconsumeIn(self.__Mode.AfterBody, token)
				elif (token.name in ["address", "article", "aside", "blockquote", "button", "center", "details", "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "listing", "main", "menu", "nav", "ol", "pre", "section", "summary", "ul"]):
					if (not self.__openElements.hasInScope(token.name)):
						pass
					else:
						# TODO: Generate implied end tags
						if (not self.__openElements.currentNode().name == token.name):
							# TODO: Handle parse error
							pass
						
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
				elif (token.name == "form"):
					if (self.__openElements.contains("template") is False):
						node = self.__formElement
						self.__formElement = None
						if (node is None or self.__openElements.hasInScope(node.name) is False):
							#TODO: Handle parse error.
							return
						self.__generateImpliedEndTags()
						if (self.__currentElement != node):
							#TODO: Handle parse error
							pass
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped(node.name)
					else:
						if (self.__openElements.hasInScope("form")):
							#TODO: Handle parse error.
							return
						self.__generateImpliedEndTags()
						if (self.__currentElementname != "form"):
							#TODO: Handle parse error
							pass
						self.__openElements.popUntilElementWithAtagNameHasBeenPopped("form")

				elif (token.name == "p"):
					if (not self.__openElements.hasInButtonScope("p")):
							element = self.__createElement(token)
							self.__openElements.push(element)
					self.__openElements.pop()
				elif (token.name == "li"):
					# TODO: Handle case
					raise NotImplementedError
				elif (token.name in ["dd", "dt"]):
					# TODO: Handle case
					raise NotImplementedError
				elif (token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
					if (not self.__openElements.hasInScope(token.name)):
						raise NotImplementedError #TODO: handle parse error.
						return
					
					if (self.__currentElement.name != token.name):
						raise NotImplementedError #TODO: handle parse error.

					while (not self.__openElements.isEmpty()):
						poppedElement = self.__openElements.pop()
						if (poppedElement.name == token.name):
							break
					return
				elif (token.name == "sarcasm"):
					# TODO: Handle case
					raise NotImplementedError
				elif (token.name in ["a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike", "strong", "tt", "u"]):
					# TODO: Run the adoption agency algorithm for the token.
					self.__adoptionAgencyAlgorithm(token)

			elif (token.type == HTMLToken.TokenType.EOF):
				for node in self.__openElements.elements():
					if node.name not in ["dd", "dt", "li", "optgroup", "option", "p", "rb", "rp", "rt", "rtc", "tbody", "td", "tfoot", "th", "thead", "tr", "body", "html"]:
						# TODO: Handle parse error.
						break
				return

		def handleText(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.Character):
				self.__insertCharacter(token)
			elif (token.type == HTMLToken.TokenType.EOF):
				if (self.__currentElement.name == "script"):
					#TODO: Mark the script element as "already started".
					pass
				self.__openElements.pop()
				self.__reconsumeIn(self.__originalInsertionMode, token)
			elif (token.type == HTMLToken.TokenType.EndTag and token.name == "script"):
					#TODO: flush_character_insertions()
					script = self.__currentElement
					self.__openElements.pop()
					self.__switchModeTo(self.__originalInsertionMode)
					#TODO: HAndle rest of the case.
			else:
				self.__openElements.pop()
				self.__switchModeTo(self.__originalInsertionMode)

		def handleInTable() -> None:
			return

		def handleInTableText() -> None:
			return

		def handleInCaption() -> None:
			return

		def handleInColumnGroup() -> None:
			return

		def handleInTableBody() -> None:
			return

		def handleInRow() -> None:
			return

		def handleInCell() -> None:
			return

		def handleInSelect() -> None:
			return

		def handleInSelectInTable() -> None:
			return

		def handleInTemplate() -> None:
			return

		def handleAfterBody(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
			if (token.type == HTMLToken.TokenType.EOF):
				self.__openElements.popAllElements()
			return

		def handleInFrameset() -> None:
			return

		def handleAfterFrameset() -> None:
			return

		def handleAfterAfterBody() -> None:
			return

		def handleAfterAfterFrameset() -> None:
			return

		switcher = {
			self.__Mode.Initial: handleInitial,
			self.__Mode.BeforeHTML: handleBeforeHTML,
			self.__Mode.BeforeHead: handleBeforeHead,
			self.__Mode.InHead: handleInHead,
			self.__Mode.InHeadNoscript: handleInHeadNoscript,
			self.__Mode.AfterHead: handleAfterHead,
			self.__Mode.InBody: handleInBody,
			self.__Mode.Text: handleText,
			self.__Mode.InTable: handleInTable,
			self.__Mode.InTableText: handleInTableText,
			self.__Mode.InCaption: handleInCaption,
			self.__Mode.InColumnGroup: handleInColumnGroup,
			self.__Mode.InTableBody: handleInTableBody,
			self.__Mode.InRow: handleInRow,
			self.__Mode.InCell: handleInCell,
			self.__Mode.InSelect: handleInSelect,
			self.__Mode.InSelectInTable: handleInSelectInTable,
			self.__Mode.InTemplate: handleInTemplate,
			self.__Mode.AfterBody: handleAfterBody,
			self.__Mode.InFrameset: handleInFrameset,
			self.__Mode.AfterFrameset: handleAfterFrameset,
			self.__Mode.AfterAfterBody: handleAfterAfterBody,
			self.__Mode.AfterAfterFrameset: handleAfterAfterFrameset,
		}

		return switcher.get(self.__currentInsertionMode, None)

	def currentInsertionMode(self) -> __Mode:
		return self.__currentInsertionMode

	def nextToken(self) -> Union[HTMLToken, None]:
		return
