from typing import Callable, Iterable, Hashable, Any

from backend.shared.event_driven.base_event import (
    Event, FieldUpdated, ItemAdded, ItemRemoved, ItemUpdated
)


class _Unset:
    def __init__(self):
        raise NotImplemented


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
        self._children: dict[Hashable, "EventNode"] = {}

    def _add_child(self, child: "EventNode"):
        if child is self:
            raise Exception(f"Circular error: {id(self)}")
        self._children[id(child)] = child

    def _remove_child(self, child: "EventNode"):
        self._children.pop(id(child), None)

    def push_event(self, event: Event):
        self._event_store.push_event(event)

    def parse_events(self) -> list[Event]:
        events = self._event_store.parse_events()
        for child in self._children.values():
            events.extend(child.parse_events())
        return events

    def __setattr__(self, key: str, new_value: Any):
        old_value = getattr(self, key, _Unset)
        if isinstance(old_value, EventNode):
            self._remove_child(old_value)

        super().__setattr__(key, new_value)

        if isinstance(new_value, EventNode):
            self._add_child(new_value)


class Property:
    def __init__(
            self,
            *,
            frozen=False,
            default: Any = _Unset,
            default_factory: Callable[[], Any] = _Unset,
            mapper: Callable[[Any], Any] = lambda x: x
    ):
        if default != _Unset and default_factory != _Unset:
            raise ValueError("Only one of default or default_factory can be set")
        self.frozen = frozen
        self.default = default
        self.default_factory = default_factory
        self.mapper = mapper
        self.private_name = None

    def __set_name__(self, owner, name):
        self.private_name = f"{name}_desc"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if hasattr(instance, self.private_name):
            return getattr(instance, self.private_name)
        else:
            default_value = self.default_factory() if self.default_factory != _Unset else self.default
            return default_value

    def __set__(self, instance: EventNode, value: Any):
        if self.frozen and hasattr(instance, self.private_name):
            raise AttributeError(f"Cannot modify frozen property {self.private_name}")

        # Здесь надо руками. Через setattr не работает (начинает отслеживать лишние поля)
        old_value = getattr(instance, self.private_name, _Unset)
        if isinstance(old_value, EventNode):
            instance._remove_child(old_value)

        value = self.mapper(value)
        instance.__dict__[self.private_name] = value

        if isinstance(value, EventNode):
            instance._add_child(value)


class PrivateProperty(Property):
    def __init__(
            self,
            *,
            frozen=False,
            default: Any = _Unset,
            default_factory: Callable[[], Any] = _Unset,
            mapper: Callable[[Any], Any] = lambda x: x,
            excluded=True,
    ):
        super().__init__(frozen=frozen, default=default, default_factory=default_factory, mapper=mapper)
        self.excluded = excluded

    def __set_name__(self, owner, name):
        if not name.startswith("_"):
            raise ValueError(f"Name for private property must start from '_'")
        self.private_name = f"{name}_desc"


class Eventable(EventNode):
    def __init__(self, **kwargs):
        self._unset_track_flag()
        super().__init__()

        for field, field_type in self.__annotations__.items():
            if field in kwargs:
                value = kwargs.pop(field)
                if field.startswith("_"):
                    prop = getattr(self.__class__, field, None)
                    if isinstance(prop, PrivateProperty) and prop.excluded:
                        raise AttributeError(f"Field '{field}' excluded from init")
            else:
                value = getattr(self, field, _Unset)
                if value == _Unset:
                    raise AttributeError(f"Argument '{field}' is required")

            setattr(self, field, value)

        if len(kwargs):
            raise AttributeError(f"Extra arguments: {list(kwargs.keys())}")

        self._set_track_flag()

    def __setuntrack__(self, key, value):
        super().__setattr__(key, value)

    def __setattr__(self, key, value):
        old_value = getattr(self, key, _Unset)
        super().__setattr__(key, value)
        if old_value != value and self._is_trackable():
            self.push_event(FieldUpdated(entity=self, old_value=old_value, new_value=value, field=key))

    def _set_track_flag(self):
        self.__dict__["__track_flag"] = True

    def _unset_track_flag(self):
        self.__dict__["__track_flag"] = False

    def _is_trackable(self) -> bool:
        return self.__dict__.get("__track_flag", False)

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
                self._add_child(value)

    def add(self, value: T):
        self._add(value, True)

    def remove(self, key: Hashable):
        item = self._items.pop(key, None)

        if item:
            self.push_event(ItemRemoved(item=item))
            if isinstance(item, EventNode):
                self._remove_child(item)

    def update(self, item: T):
        # Проверяем, что он существует
        key = self._key(item)
        self.get(key)

        # Не забываем отписаться от ноды
        removed = self._items.pop(key)
        if isinstance(removed, EventNode):
            self._remove_child(removed)

        # Вставляем новый объект
        self._items[key] = item
        self.push_event(ItemUpdated(old_item=removed, new_item=item))
        if isinstance(item, EventNode):
            self._add_child(item)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for item in self._items.values():
            yield item
