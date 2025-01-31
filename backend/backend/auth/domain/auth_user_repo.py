from abc import ABC, abstractmethod

from backend.auth.domain.auth_user import AuthUserCreate, AuthId, AuthUser


class AuthUserRepo(ABC):
    @abstractmethod
    async def get_one_by_id(self, item_id: AuthId) -> AuthUser:
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
