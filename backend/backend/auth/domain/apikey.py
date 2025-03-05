import secrets
from abc import ABC, abstractmethod
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.shared.base_models import MyBase, BaseSby
from backend.shared.enums import Lock
from backend.shared.utils import get_current_datetime

ApikeyId = UUID


class Apikey(MyBase):
    id: ApikeyId = Field(default_factory=uuid4)
    title: str
    auth_user: AuthUser
    value: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)

    def to_light_bson(self):
        result = self.model_dump(exclude={"value", "auth_user"}, mode="json")
        return result


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
