from typing import Iterable, Hashable, TypeVar, Generic

T = TypeVar("T")


class ItemManager(Generic[T]):
    def __init__(self, items: Iterable, key=None):
        self._key = key
        self._items: dict[Hashable, T] = {}

        for item in items:
            self.add(item)

    def add(self, item: T) -> None:
        key = item.__getattribute__(self._key) if self._key else item
        if key in self._items:
            raise ValueError
        self._items[key] = item

    def update(self, item: T) -> None:
        key = item.__getattribute__(self._key) if self._key else item
        self.get(key)
        self._items[key] = item

    def get(self, key: Hashable) -> T:
        return self._items[key]

    def get_all(self) -> list[T]:
        return list(self._items.values())

    def remove(self, key: Hashable) -> None:
        self._items.pop(key, None)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for item in self._items.values():
            yield item
