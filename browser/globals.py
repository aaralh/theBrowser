from typing import List
from uuid import UUID
from utils import log

from browser.Inspector import Inspector


HSTEP, VSTEP = 13, 18
EMOJIS_PATH = "resources/emojis/"


class BrowserState():
    __current_url: str = ""
    __inspectors: List[Inspector] = []
    __selected_elements: List[UUID] = []

    @staticmethod
    def set_selected_elements(element_ids: List[UUID]) -> None:
        BrowserState.__selected_elements = element_ids
        log("Selected items:", BrowserState.__selected_elements)

    @staticmethod
    def remove_selected_element(element_id: UUID) -> None:
        BrowserState.__selected_elements.remove(element_id)
    
    @staticmethod
    def get_selected_elements() -> List[UUID]:
        return BrowserState.__selected_elements

    @staticmethod
    def get_current_url() -> str:
        return BrowserState.__current_url

    @staticmethod
    def set_current_url(url: str) -> None:
        BrowserState.__current_url = url

    @staticmethod
    def get_inspectors() -> List[Inspector]:
        return BrowserState.__inspectors

    @staticmethod
    def register_inspector(inspector: Inspector) -> None:
        BrowserState.__inspectors.append(inspector)
    
    @staticmethod
    def remove_inspector(inspector: Inspector) -> None:
        BrowserState.__inspectors.remove(inspector)
    