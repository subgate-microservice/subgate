from abc import ABC, abstractmethod

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.shared.base_models import MyBase, BaseSby
from backend.shared.enums import Lock
from backend.shared.utils.dt import get_current_datetime


class Apikey(MyBase):
    public_id: str
    title: str
    auth_user: AuthUser
    hashed_secret: str
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)


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
    async def get_one_by_public_id(self, public_id: str) -> Apikey:
        raise NotImplemented

    @abstractmethod
    async def delete_one(self, item: Apikey) -> None:
        raise NotImplemented
