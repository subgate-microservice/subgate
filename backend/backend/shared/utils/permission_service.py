from typing import Protocol, Hashable


class HasAuth(Protocol):
    auth_id: Hashable


def check_item_owner(item: HasAuth, owner_id: Hashable) -> None:
    if item.auth_id != owner_id:
        raise PermissionError
