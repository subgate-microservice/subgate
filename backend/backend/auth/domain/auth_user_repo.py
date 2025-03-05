from abc import ABC, abstractmethod

from backend.auth.domain.auth_user import AuthId, AuthUser
from backend.auth.application.auth_usecases import AuthUserCreate


class AuthUserRepo(ABC):
    @abstractmethod
    async def get_one_by_id(self, item_id: AuthId) -> AuthUser:
        pass

    @abstractmethod
    async def get_one_by_username(self, username: str) -> AuthUser:
        pass

    @abstractmethod
    async def add_one(self, item: AuthUserCreate) -> AuthId:
        pass

    @abstractmethod
    async def update_one(self, item: AuthUser) -> None:
        pass

    @abstractmethod
    async def delete_one(self, item:  AuthUser) -> None:
        pass
