from typing import Iterable, Callable, Hashable, Protocol

from backend.shared.event_driven.eventable import EventableSet


class HasCode(Protocol):
    code: Hashable


class ItemManager[T](EventableSet):
    def __init__(
            self,
            items: Iterable[HasCode] = None,
            key: Callable[[HasCode], Hashable] = lambda x: x.code,
            prevent_duplicates=True,
    ):
        super().__init__(items, key, prevent_duplicates)
