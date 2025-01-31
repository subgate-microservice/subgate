from abc import ABC
from typing import Optional, Protocol, Any

from backend.auth.domain.auth_user import AuthId, AuthUser


class HasAuthId(Protocol):
    auth_id: AuthId


class HasAuthIds(Protocol):
    auth_ids: Optional[set[AuthId]] = None


class SubscriptionClient(Protocol):
    async def get_user_active_subscription(self, target_id: str) -> Optional[Any]:
        raise NotImplemented


class PermissionService(ABC):
    def __init__(self, sub_service_client: SubscriptionClient):
        self._sub_service_client = sub_service_client

    @staticmethod
    def check_auth_user_is_item_owner(item: HasAuthId, auth: AuthUser) -> None:
        if item.auth_id != auth.id:
            raise PermissionError

    async def check_auth_user_can_get(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            self.check_auth_user_is_item_owner(item, auth)

    async def check_auth_user_can_get_many(self, sby: HasAuthIds, auth: AuthUser) -> None:
        if not auth.is_admin():
            if sby.auth_ids is None:
                raise PermissionError("auth_id is None")

            if len(sby.auth_ids) != 1:
                raise PermissionError("incorrect auth_ids length")

            if next(x for x in sby.auth_ids) != auth.id:
                raise PermissionError(f"{next(x for x in sby.auth_ids)} != {auth.id}")

    async def check_auth_user_can_delete_many(self, sby: HasAuthIds, auth: AuthUser) -> None:
        await self.check_auth_user_can_get_many(sby, auth)

    async def check_auth_user_can_create(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            self.check_auth_user_is_item_owner(item, auth)

    async def check_auth_user_can_update(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            self.check_auth_user_is_item_owner(item, auth)

    async def check_auth_user_can_delete(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            self.check_auth_user_is_item_owner(item, auth)


class AdminOnlyPermissionService(PermissionService):
    async def check_auth_user_can_get(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            raise PermissionError("Only admin user can do this action")

    async def check_auth_user_can_get_many(self, sby: HasAuthIds, auth: AuthUser) -> None:
        if not auth.is_admin():
            raise PermissionError("Only admin user can do this action")

    async def check_auth_user_can_create(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            raise PermissionError("Only admin user can do this action")

    async def check_auth_user_can_update(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            raise PermissionError("Only admin user can do this action")

    async def check_auth_user_can_delete(self, item: HasAuthId, auth: AuthUser) -> None:
        if not auth.is_admin():
            raise PermissionError("Only admin user can do this action")
