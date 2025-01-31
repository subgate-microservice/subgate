from collections import defaultdict
from typing import Callable, Awaitable, Optional


class Event[P, C]:
    def __init__(
            self,
            code: str,
            payload: Optional[P] = None,
            context: Optional[C] = None,
    ):
        self.code = code
        self.payload = payload
        self.context = context

    def __str__(self):
        return f"{self.code}(payload={self.payload})"

    def __repr__(self):
        return f"{self.code}(payload={self.payload})"


Subscriber = Callable[[Event], Awaitable]


class Eventbus:
    def __init__(self):
        self._subs: defaultdict[str, list[Subscriber]] = defaultdict(list)

    def subscribe(self, event_code: str, subscriber: Subscriber):
        self._subs[event_code].append(subscriber)

    def unsubscribe(self, event_code: str, subscriber: Subscriber):
        self._subs[event_code].remove(subscriber)

    async def publish(self, event: Event):
        for subscriber in self._subs[event.code]:
            await subscriber(event)
