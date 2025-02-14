from typing import Callable, Type, Awaitable

from backend.shared.event_driven.base_event import Event
from backend.shared.unit_of_work.uow import UnitOfWork


class Context:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow


Subscriber = Callable[[Event, Context], Awaitable[None]]


class Bus:
    def __init__(self):
        self._subscribers: dict[Type[Event], set[Subscriber]] = {}

    def subscribe(self, event_type: Type[Event], subscriber: Subscriber) -> None:
        self._subscribers.setdefault(event_type, set()).add(subscriber)

    async def publish(self, event: Event, context: Context) -> None:
        subscribers = self._subscribers.get(event.__class__, set())
        for sub in subscribers:
            await sub(event, context)

    async def publish_from_unit_of_work(self, uow: UnitOfWork):
        while True:
            new_events = uow.parse_events()
            if not new_events:
                break

            for ev in new_events:
                await self.publish(ev, Context(uow))
