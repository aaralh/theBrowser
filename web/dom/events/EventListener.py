from web.dom.events.Event import Event


class EventListener:
    def handle_event(self, event: Event) -> None:
        raise NotImplementedError
