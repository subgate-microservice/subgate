from abc import ABC, abstractmethod

from pydantic import Field

from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.shared.base_models import MyBase


class AuthUserCreate(MyBase):
    email: str
    password: str
    email_verified: bool = Field(default=False)


class AuthUserPasswordUpdate(MyBase):
    id: AuthId
    old_password: str
    new_password: str


class AuthUserEmailUpdate(MyBase):
    id: AuthId
    new_email: str
    password: str


class AuthUserDelete(MyBase):
    id: AuthId
    password: str


class AuthUsecase(ABC):
    @abstractmethod
    async def get_auth_user_by_email(self, email: str) -> AuthUser:
        raise NotImplemented

    @abstractmethod
    async def get_auth_user_by_id(self, id: AuthId) -> AuthUser:
        raise NotImplemented

    @abstractmethod
    async def create_auth_user(self, data: AuthUserCreate) -> AuthUser:
        raise NotImplemented

    @abstractmethod
    async def delete_auth_user(self, data: AuthUserDelete) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_email(self, data: AuthUserEmailUpdate) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_password(self, data: AuthUserPasswordUpdate) -> None:
        raise NotImplemented
