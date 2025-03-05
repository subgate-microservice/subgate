from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from backend.shared.base_models import MyBase

AuthId = UUID


class AuthRole(StrEnum):
    Admin = "subtrack:admin"


class AuthUser(MyBase):
    id: AuthId = Field(default_factory=uuid4)
