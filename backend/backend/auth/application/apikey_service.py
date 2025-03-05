import secrets
from typing import Optional
from uuid import uuid4

import bcrypt
from pydantic import Field

from backend.auth.domain.apikey import Apikey, ApikeyRepo, ApikeyId
from backend.auth.domain.auth_user import AuthUser
from backend.auth.domain.exceptions import AuthenticationError
from backend.shared.base_models import MyBase


class ApikeyCreate(MyBase):
    id: ApikeyId = Field(default_factory=uuid4)
    title: str
    auth_user: AuthUser
    public_id: str = Field(default_factory=lambda: f"apikey_{uuid4().hex[:8]}")
    secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))


class ApikeyCreateResult(MyBase):
    public_id: str
    secret: str


class ApikeyManager:
    def __init__(self, repo: ApikeyRepo):
        self._repo = repo

    async def _check(self, apikey_secret: str) -> Optional[Apikey]:
        try:
            public_id, secret = apikey_secret.split(":")
            apikey = await self._repo.get_one_by_public_id(public_id)

            apikey_secret_is_valid = bcrypt.checkpw(secret.encode(), apikey.hashed_secret.encode())
            if apikey_secret_is_valid:
                return apikey
        except LookupError:
            return None
        except ValueError:
            return None

    async def create(self, data: ApikeyCreate):
        hashed_secret = bcrypt.hashpw(data.secret.encode(), bcrypt.gensalt()).decode()

        apikey = Apikey(id=data.id, title=data.title, auth_user=data.auth_user, public_id=data.public_id,
                        hashed_secret=hashed_secret)
        await self._repo.add_one(apikey)

    async def get_by_secret(self, apikey_secret: str) -> Apikey:
        result = await self._check(apikey_secret)
        if not result:
            raise AuthenticationError()
        return result
