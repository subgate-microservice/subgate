from typing import Any

from pydantic import BaseModel, ConfigDict


class Event(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    @property
    def event_code(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.event_code}"


class FieldUpdated[T](Event):
    entity: Any
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
    def from_field_updates(cls, events: list[FieldUpdated]):
        entity = events[0].entity
        updated_fields: dict[str, tuple[Any, Any]] = {}
        for ev in events:
            if entity is not ev.entity:
                raise TypeError
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
