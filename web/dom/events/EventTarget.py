from typing import Optional, Callable
from web.dom.types import DOMString


class EventTarget:
    """
    An EventTarget object represents a target to which an event can be dispatched when something has occurred.
    """

    def __init__(self) -> None:
        pass

    def add_event_listener(self, event_type: DOMString, event_listener: Optional[Callable]) -> None:
        raise NotImplementedError
