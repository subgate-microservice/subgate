from typing import Any, Callable, Iterable, Hashable, Union

from backend.shared.event_driven.base_event import Event


class FieldUpdated[T](Event):
    field: str
    old_value: T
    new_value: T


class EntityCreated[T](Event):
    entity: T


class EntityDeleted[T](Event):
    entity: T


class EntityUpdated[T](Event):
    entity: T
    updated_fields: dict[str, tuple[Any, Any]]

    @classmethod
    def from_field_updates(cls, entity: Any, events: list[FieldUpdated]):
        updated_fields: dict[str, tuple[Any, Any]] = {}
        for ev in events:
            old_value = updated_fields[ev.field][0] if ev.field in updated_fields else ev.old_value
            updated_fields[ev.field] = (old_value, ev.new_value)
        return cls(entity=entity, updated_fields=updated_fields)


class ItemAdded[T](Event):
    item: T


class ItemRemoved[T](Event):
    item: T


class ItemUpdated[T](Event):
    new_item: T
    old_item: T


CollectionEvent = Union[ItemAdded, ItemUpdated, ItemRemoved]


class EventStore:
    def __init__(self):
        self._field_updated_events: list[FieldUpdated] = []
        self._collection_events: list[CollectionEvent] = []
        self._other_events: list[Event] = []

    @property
    def total_len(self):
        return len(self._field_updated_events) + len(self._other_events) + len(self._collection_events)

    def push_event(self, event: Event):
        if isinstance(event, FieldUpdated):
            self._field_updated_events.append(event)
        elif isinstance(event, CollectionEvent):
            self._collection_events.append(event)
        else:
            self._other_events.append(event)

    def parse_field_updated_events(self) -> list[FieldUpdated]:
        events = self._field_updated_events
        self._field_updated_events = []
        return events

    def parse_collection_events(self) -> list[CollectionEvent]:
        events = self._collection_events
        self._collection_events = []
        return events

    def parse_other_events(self) -> list[Event]:
        events = self._other_events
        self._other_events = []
        return events

    def parse_all_events(self):
        events = [
            *self.parse_field_updated_events(),
            *self.parse_other_events(),
        ]
        return events


class EventNode:
    def __init__(self):
        self._event_store = EventStore()
        self._children: set["EventNode"] = set()

    @property
    def event_store(self) -> EventStore:
        return self._event_store

    def add_child(self, child: "EventNode"):
        self._children.add(child)

    def get_children(self) -> set["EventNode"]:
        return self._children

    def remove_child(self, child: "EventNode"):
        self._children.remove(child)

    def traverse(self, callback: Callable[["EventNode"], None]):
        callback(self)
        for child in self.get_children():
            child.traverse(callback)


class Property:
    def __init__(self, default_factory: Callable[[], Any] = None):
        self.default_factory = default_factory


UNTRACKABLE = {"_event_node", "_track_flag"}


class Eventable:
    _track_flag = False

    def __init__(self, **kwargs):
        self._event_node = EventNode()

        for field in self.__class__.__annotations__:
            if field not in kwargs:
                default_value = self.__getattribute__(field)
                if isinstance(default_value, Property):
                    if default_value.default_factory:
                        default_value = default_value.default_factory()
                value = default_value
            else:
                value = kwargs[field]
            super().__setattr__(field, value)

            if isinstance(value, Eventable):
                self._event_node.add_child(value._event_node)

        self._start_tracking()

    def push_event(self, event: Event) -> None:
        self._event_node.event_store.push_event(event)

    def parse_events(self) -> list[Event]:
        events = []

        def callback(node: EventNode) -> None:
            field_updated_events = node.event_store.parse_field_updated_events()
            if field_updated_events:
                events.append(
                    EntityUpdated.from_field_updates(self, field_updated_events)
                )
            events.extend(node.event_store.parse_other_events())
            events.extend(node.event_store.parse_collection_events())
            assert node.event_store.total_len == 0

        self.get_event_node().traverse(callback)
        return events

    def get_event_node(self) -> EventNode:
        return self._event_node

    def _stop_tracking(self):
        self._track_flag = False

    def _start_tracking(self):
        self._track_flag = True

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, key, value):
        if self._track_flag and key not in UNTRACKABLE:
            old_value = self.__getattribute__(key)
            self.get_event_node().event_store.push_event(
                FieldUpdated(field=key, old_value=old_value, new_value=value)
            )
        super().__setattr__(key, value)

    def __setuntrack__(self, key, value):
        super().__setattr__(key, value)


class EventableSet[T](Eventable):
    _items: dict[Hashable, T] = None
    _key: Callable[[T], Hashable] = None
    _prevent_duplicates: bool = None

    def __init__(
            self,
            items: Iterable[T] = None,
            key: Callable[[T], Hashable] = lambda x: x,
            prevent_duplicates=False,
    ):
        super().__init__()
        items = items or []
        d = {}

        for item in items:
            d[key(item)] = item
            if isinstance(item, Eventable):
                self.get_event_node().add_child(item.get_event_node())

        self.__setuntrack__("_items", d)
        self.__setuntrack__("_key", key)
        self.__setuntrack__("_prevent_duplicates", prevent_duplicates)

        if prevent_duplicates:
            if len(self._items) < len(items):
                raise ValueError

    def get(self, key: Hashable) -> T:
        return self._items[key]

    def get_all(self) -> list[T]:
        return list(self._items.values())

    def add(self, value: T):
        key = self._key(value)
        if key in self._items and self._prevent_duplicates:
            raise ValueError(key)

        event_class = ItemUpdated if key in self._items else ItemAdded

        self._items[key] = value
        self.push_event(event_class(item=value))
        if isinstance(value, Eventable):
            self.get_event_node().add_child(value.get_event_node())

    def remove(self, key: Hashable):
        item = self._items.pop(key, None)

        if item:
            self.push_event(ItemRemoved(item=item))
            if isinstance(item, Eventable):
                self.get_event_node().remove_child(item.get_event_node())

    def update(self, item: T):
        # Проверяем, что он существует
        key = self._key(item)
        self.get(key)

        # Не забываем отписаться от ноды
        removed = self._items.pop(key)
        if isinstance(removed, Eventable):
            self.get_event_node().remove_child(removed.get_event_node())

        # Вставляем новый объект
        self._items[key] = item
        self.push_event(ItemUpdated(old_item=removed, new_item=item))
        if isinstance(item, Eventable):
            self.get_event_node().add_child(item.get_event_node())

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for item in self._items.values():
            yield item
