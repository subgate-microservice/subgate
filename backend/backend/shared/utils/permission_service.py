from typing import Protocol, Hashable


class HasId(Protocol):
    id: Hashable


def check_item_owner(item: HasId, owner_id: Hashable) -> None:
    if item.id != owner_id:
        raise PermissionError
