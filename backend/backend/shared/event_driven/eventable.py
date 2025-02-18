from typing import Any, Callable, Iterable, Hashable, Optional, Self

from backend.shared.event_driven.base_event import (
    Event, FieldUpdated, ItemAdded, ItemRemoved, ItemUpdated
)


class EventStore:
    def __init__(self):
        self._events: list[Event] = []

    def push_event(self, event: Event):
        self._events.append(event)

    def parse_events(self) -> list[Event]:
        events = self._events
        self._events = []
        return events

    def get_events(self) -> list[Event]:
        return self._events

    def __len__(self):
        return len(self._events)


class Property:
    def __init__(self, default_factory: Callable[[], Any] = None):
        self.default_factory = default_factory


class EventNode:
    def __init__(self):
        self._event_store = EventStore()
        self._parent: Optional[Self] = None

    def _set_parent(self, parent: Self):
        if self._parent:
            raise ValueError("This object already has a parent node")
        self._parent = parent
        if len(self._event_store):
            for ev in self._event_store.parse_events():
                self._parent.push_event(ev)

    def _unset_parent(self):
        self._parent = None

    def push_event(self, event: Event):
        if self._parent:
            self._parent.push_event(event)
        else:
            self._event_store.push_event(event)

    def parse_events(self) -> list[Event]:
        return self._event_store.parse_events()


class Eventable(EventNode):
    def __init__(self, **kwargs):
        self._unset_track_flag()
        super().__init__()
        for field, field_type in self.__class__.__annotations__.items():
            value = kwargs[field]
            self.__setuntrack__(field, value)
            if isinstance(value, EventNode):
                value._set_parent(self)
        self._set_track_flag()

    def __setuntrack__(self, key, value):
        super().__setattr__(key, value)

    def __setattr__(self, key, value):
        if self._is_trackable():
            old_value = self.__getattribute__(key)
            super().__setattr__(key, value)
            self.push_event(FieldUpdated(entity=self, old_value=old_value, new_value=value, field=key))
        else:
            super().__setattr__(key, value)

    def _set_track_flag(self):
        self.__dict__["__track_flag"] = True

    def _unset_track_flag(self):
        self.__dict__["__track_flag"] = False

    def _is_trackable(self) -> bool:
        return self.__dict__.get("__track_flag", False)

    def _set_parent(self, parent: Self):
        self.__setuntrack__("_parent", parent)

    def _unset_parent(self):
        self.__setuntrack__("_parent", None)

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()


class EventableSet[T](EventNode):
    def __init__(
            self,
            items: Iterable[T] = None,
            key: Callable[[T], Hashable] = lambda x: x,
            prevent_duplicates=False,
    ):
        super().__init__()
        self._items: dict[Hashable, T] = {}
        self._key = key
        self._prevent_duplicates = prevent_duplicates

        if items:
            for item in items:
                self._add(item, False)

    def get(self, key: Hashable) -> T:
        return self._items[key]

    def get_all(self) -> list[T]:
        return list(self._items.values())

    def _add(self, value: T, push_event=True):
        key = self._key(value)
        if key in self._items:
            if self._prevent_duplicates:
                raise ValueError(key)
            else:
                return

        self._items[key] = value
        if push_event:
            self.push_event(ItemAdded(item=value))
            if isinstance(value, EventNode):
                value._set_parent(self)

    def add(self, value: T):
        self._add(value, True)

    def remove(self, key: Hashable):
        item = self._items.pop(key, None)

        if item:
            self.push_event(ItemRemoved(item=item))
            if isinstance(item, EventNode):
                item._unset_parent()

    def update(self, item: T):
        # Проверяем, что он существует
        key = self._key(item)
        self.get(key)

        # Не забываем отписаться от ноды
        removed = self._items.pop(key)
        if isinstance(removed, Eventable):
            removed._unset_parent()

        # Вставляем новый объект
        self._items[key] = item
        self.push_event(ItemUpdated(old_item=removed, new_item=item))
        if isinstance(item, EventNode):
            item._set_parent(self)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for item in self._items.values():
            yield item
