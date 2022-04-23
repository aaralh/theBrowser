HSTEP, VSTEP = 13, 18
EMOJIS_PATH = "resources/emojis/"


class BrowserState():
    __current_url: str = ""

    @staticmethod
    def get_current_url() -> str:
        return BrowserState.__current_url

    @staticmethod
    def set_current_url(url: str) -> None:
        BrowserState.__current_url = url
    