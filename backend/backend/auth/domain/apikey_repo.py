from abc import ABC, abstractmethod

from backend.auth.domain.apikey import Apikey, ApikeyId
from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import BaseSby
from backend.shared.enums import Lock


class ApikeySby(BaseSby):
    auth_ids: set[AuthId]


class ApikeyRepo(ABC):
    @abstractmethod
    async def add_one(self, item: Apikey):
        raise NotImplemented

    @abstractmethod
    async def get_selected(self, sby: ApikeySby, lock: Lock = "write") -> list[Apikey]:
        raise NotImplemented

    @abstractmethod
    async def get_one_by_id(self, item_id: ApikeyId, lock: Lock = "write") -> Apikey:
        raise NotImplemented

    @abstractmethod
    async def get_apikey_by_value(self, apikey_value: str, lock: Lock = "write") -> Apikey:
        raise NotImplemented

    @abstractmethod
    async def delete_one(self, item: Apikey) -> None:
        raise NotImplemented
