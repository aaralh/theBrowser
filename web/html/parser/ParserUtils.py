class ParserUtils:

    @staticmethod
    def isSpecialtag(tagName: str, namespace: str) -> bool:

        if namespace == "html":
            return tagName in ["address", "applet", "area", "article", "aside", "base", "basefont", "bgsound",
                               "blockquote",
                               "body", "br", "button", "caption", "center", "col", "colgroup", "dd", "details", "dir",
                               "div",
                               "dl", "dt", "embed", "fieldset", "figcaption", "figure", "footer", "form", "frame",
                               "frameset",
                               "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html", "iframe",
                               "img",
                               "input", "keygen", "li", "link", "listing", "main", "marquee", "menu", "meta", "nav",
                               "noembed",
                               "noframes", "noscript", "object", "ol", "p", "param", "plaintext", "pre", "script",
                               "section",
                               "select", "source", "style", "summary", "table", "tbody", "td", "template_", "textarea",
                               "tfoot",
                               "th", "thead", "title", "tr", "track", "ul", "wbr", "xmp"]
        elif namespace == "svg":
            return tagName in ["desc", "foreignObject", "title"]

        elif namespace == "mathml":
            # TODO: Handle case
            raise NotImplementedError

        return False
