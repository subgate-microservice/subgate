from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from backend.shared.base_models import MyBase

AuthId = UUID


class AuthRole(StrEnum):
    Admin = "subtrack:admin"


class AuthUser(MyBase):
    id: AuthId = Field(default_factory=uuid4)
    roles: set[AuthRole] = Field(default_factory=set)

    def is_admin(self) -> bool:
        return AuthRole.Admin in self.roles


class AuthUserCreate(MyBase):
    email: str
    password: str
    email_verified: bool = Field(default=False)
