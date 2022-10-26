from typing import Callable, TYPE_CHECKING, Dict
from web.dom import elements
from web.dom.Node import Node
from web.html.parser.HTMLToken import HTMLTag
from web.dom.Document import Document

if TYPE_CHECKING:
    from web.dom.elements.Element import Element

TAG_NAMES: Dict[str, Callable[[HTMLTag, Node, Document], "Element"]] = {
    "a": elements.HTMLAElement,
    "abbr": elements.HTMLAbbrElement,
    "acronym": elements.HTMLAcronymElement,
    "address": elements.HTMLAddressElement,
    "applet": elements.HTMLAppletElement,
    "area": elements.HTMLAreaElement,
    "article": elements.HTMLArticleElement,
    "aside": elements.HTMLAsideElement,
    "audio": elements.HTMLAudioElement,
    "b": elements.HTMLBElement,
    "base": elements.HTMLBaseElement,
    "basefont": elements.HTMLBasefontElement,
    "bdi": elements.HTMLBdiElement,
    "bdo": elements.HTMLBdoElement,
    "bgsound": elements.HTMLBgsoundElement,
    "big": elements.HTMLBigElement,
    "blink": elements.HTMLBlinkElement,
    "blockquote": elements.HTMLBlockquoteElement,
    "body": elements.HTMLBodyElement,
    "br": elements.HTMLBrElement,
    "button": elements.HTMLButtonElement,
    "canvas": elements.HTMLCanvasElement,
    "caption": elements.HTMLCaptionElement,
    "center": elements.HTMLCenterElement,
    "cite": elements.HTMLCiteElement,
    "clippath": elements.HTMLClipPathElement,
    "code": elements.HTMLCodeElement,
    "col": elements.HTMLColElement,
    "colgroup": elements.HTMLColgroupElement,
    "data": elements.HTMLDataElement,
    "datalist": elements.HTMLDatalistElement,
    "dd": elements.HTMLDdElement,
    "defs": elements.HTMLDefsElement,
    "del": elements.HTMLDelElement,
    "details": elements.HTMLDetailsElement,
    "dfn": elements.HTMLDfnElement,
    "dialog": elements.HTMLDialogElement,
    "dir": elements.HTMLDirElement,
    "div": elements.HTMLDivElement,
    "dl": elements.HTMLDlElement,
    "dt": elements.HTMLDtElement,
    "em": elements.HTMLEmElement,
    "embed": elements.HTMLEmbedElement,
    "fieldset": elements.HTMLFieldsetElement,
    "figcaption": elements.HTMLFigcaptionElement,
    "figure": elements.HTMLFigureElement,
    "filter": elements.HTMLFilterElement,
    "font": elements.HTMLFontElement,
    "footer": elements.HTMLFooterElement,
    "form": elements.HTMLFormElement,
    "frame": elements.HTMLFrameElement,
    "frameset": elements.HTMLFramesetElement,
    "g": elements.HTMLGElement,
    "h1": elements.HTMLH1Element,
    "h2": elements.HTMLH2Element,
    "h3": elements.HTMLH3Element,
    "h4": elements.HTMLH4Element,
    "h5": elements.HTMLH5Element,
    "h6": elements.HTMLH6Element,
    "head": elements.HTMLHeadElement,
    "header": elements.HTMLHeaderElement,
    "hgroup": elements.HTMLHgroupElement,
    "hr": elements.HTMLHrElement,
    "html": elements.HTMLElement,
    "i": elements.HTMLIElement,
    "iframe": elements.HTMLIframeElement,
    "image": elements.HTMLImageElement,
    "img": elements.HTMLImgElement,
    "input": elements.HTMLInputElement,
    "ins": elements.HTMLInsElement,
    "kbd": elements.HTMLKbdElement,
    "keygen": elements.HTMLKeygenElement,
    "label": elements.HTMLLabelElement,
    "legend": elements.HTMLLegendElement,
    "li": elements.HTMLLiElement,
    "lineargradient": elements.HTMLLinearGradientElement,
    "link": elements.HTMLLinkElement,
    "listing": elements.HTMLListingElement,
    "main": elements.HTMLMainElement,
    "map": elements.HTMLMapElement,
    "mark": elements.HTMLMarkElement,
    "marquee": elements.HTMLMarqueeElement,
    "math": elements.HTMLMathElement,
    "menu": elements.HTMLMenuElement,
    "meta": elements.HTMLMetaElement,
    "meter": elements.HTMLMeterElement,
    "nav": elements.HTMLNavElement,
    "nobr": elements.HTMLNobrElement,
    "noembed": elements.HTMLNoembedElement,
    "noframes": elements.HTMLNoframesElement,
    "noscript": elements.HTMLNoscriptElement,
    "object": elements.HTMLObjectElement,
    "ol": elements.HTMLOlElement,
    "optgroup": elements.HTMLOptgroupElement,
    "option": elements.HTMLOptionElement,
    "output": elements.HTMLOutputElement,
    "p": elements.HTMLPElement,
    "param": elements.HTMLParamElement,
    "picture": elements.HTMLPictureElement,
    "path": elements.HTMLPathElement,
    "plaintext": elements.HTMLPlaintextElement,
    "pre": elements.HTMLPreElement,
    "progress": elements.HTMLProgressElement,
    "q": elements.HTMLQElement,
    "ruby": elements.HTMLRubyElement,
    "rb": elements.HTMLRbElement,
    "rp": elements.HTMLRpElement,
    "rt": elements.HTMLRtElement,
    "rtc": elements.HTMLRtcElement,
    "s": elements.HTMLSElement,
    "samp": elements.HTMLSampElement,
    "script": elements.HTMLScriptElement,
    "section": elements.HTMLSectionElement,
    "select": elements.HTMLSelectElement,
    "slot": elements.HTMLSlotElement,
    "small": elements.HTMLSmallElement,
    "source": elements.HTMLSourceElement,
    "span": elements.HTMLSpanElement,
    "strike": elements.HTMLStrikeElement,
    "strong": elements.HTMLStrongElement,
    "stop": elements.HTMLStopElement,
    "style": elements.HTMLStyleElement,
    "sub": elements.HTMLSubElement,
    "sup": elements.HTMLSupElement,
    "summary": elements.HTMLSummaryElement,
    "svg": elements.HTMLSvgElement,
    "table": elements.HTMLTableElement,
    "tbody": elements.HTMLTbodyElement,
    "td": elements.HTMLTdElement,
    "template": elements.HTMLTemplateElement,
    "textarea": elements.HTMLTextareaElement,
    "tfoot": elements.HTMLTfootElement,
    "th": elements.HTMLThElement,
    "thead": elements.HTMLTheadElement,
    "time": elements.HTMLTimeElement,
    "title": elements.HTMLTitleElement,
    "tr": elements.HTMLTrElement,
    "track": elements.HTMLTrackElement,
    "tt": elements.HTMLTtElement,
    "u": elements.HTMLUElement,
    "ul": elements.HTMLUlElement,
    "var": elements.HTMLVarElement,
    "video": elements.HTMLVideoElement,
    "wbr": elements.HTMLWbrElement,
    "xmp": elements.HTMLXmpElement,
    "xml": elements.HTMLXmlElement,
}
