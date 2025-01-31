from backend.auth.domain.apikey import Apikey, ApikeyId
from backend.auth.domain.apikey_repo import ApikeySby
from backend.auth.domain.auth_user import AuthUser
from backend.shared.unit_of_work.uow import UnitOfWork


class ApikeyService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def create_one(self, item: Apikey) -> None:
        await self._uow.apikey_repo().add_one(item)

    async def get_selected(self, sby: ApikeySby) -> list[Apikey]:
        return await self._uow.apikey_repo().get_selected(sby)

    async def get_one_by_id(self, item_id: ApikeyId) -> Apikey:
        return await self._uow.apikey_repo().get_one_by_id(item_id)

    async def delete_one(self, item: Apikey) -> None:
        await self._uow.apikey_repo().delete_one(item)

    async def get_auth_user_by_apikey_value(self, apikey_value: str) -> AuthUser:
        return await self._uow.apikey_repo().get_apikey_by_value(apikey_value)
