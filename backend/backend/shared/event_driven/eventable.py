from typing import Callable, Iterable, Hashable, Optional, Self, Any

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


class Property:
    def __init__(self, *, frozen=False, default=None, default_factory=None, mapper: Callable[[Any], Any] = lambda x: x):
        if default is not None and default_factory is not None:
            raise ValueError("Only one of default or default_factory can be set")
        self.frozen = frozen
        self.default = default
        self.default_factory = default_factory
        self.mapper = mapper
        self.private_name = None

    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name,
                       self.default if self.default_factory is None else self.default_factory())

    def __set__(self, instance, value):
        if self.frozen and hasattr(instance, self.private_name):
            raise AttributeError(f"Cannot modify frozen property {self.private_name}")
        setattr(instance, self.private_name, self.mapper(value))


class Eventable(EventNode):
    def __init__(self, **kwargs):
        self._unset_track_flag()
        super().__init__()

        for field, field_type in self.__annotations__.items():
            if field in kwargs:
                value = kwargs.pop(field)
            else:
                try:
                    value = getattr(self, field)
                except AttributeError:
                    raise AttributeError(f"Argument '{field}' is required")
            setattr(self, field, value)

        self._set_track_flag()

    def __setuntrack__(self, key, value):
        super().__setattr__(key, value)

    def __setattr__(self, key, value):
        old_value = getattr(self, key, None)
        super().__setattr__(key, value)
        if isinstance(old_value, EventNode):
            old_value._unset_parent()
        if isinstance(value, EventNode):
            value._set_parent(self)
        if self._is_trackable():
            self.push_event(FieldUpdated(entity=self, old_value=old_value, new_value=value, field=key))

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
        if isinstance(removed, EventNode):
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


class Foo(Eventable):
    frozen_value: int = Property(frozen=True)
    maps: int


def main():
    foo = Foo(frozen_value=100, )
    # print(foo.maps)


if __name__ == "__main__":
    main()
