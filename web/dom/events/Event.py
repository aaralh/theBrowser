from dataclasses import dataclass
from typing import Optional

from web.dom.events.EventTarget import EventTarget
from web.dom.types import DOMString


@dataclass
class EventInit:
    bubbles: bool = False,
    cancelable: bool = False,
    composed: bool = False


class Event:

    def __init__(self, event_type: DOMString, event_init_dict: EventInit = EventInit()) -> None:
        self.__event_type = event_type
        self.__bubbles = event_init_dict.bubbles
        self.__cancelable = event_init_dict.cancelable
        self.__composed = event_init_dict.composed

        self.__target: Optional[EventTarget] = None
        self.__current_target: Optional[EventTarget] = None

    @property
    def bubbles(self) -> bool:
        return self.__bubbles

    @property
    def cancelable(self) -> bool:
        return self.__cancelable

    @property
    def composed(self) -> bool:
        return self.__composed

    @property
    def target(self) -> Optional[EventTarget]:
        return self.__target

    @target.setter
    def target(self, target: EventTarget) -> None:
        self.__target = target

    @property
    def current_target(self) -> Optional[EventTarget]:
        return self.__current_target
