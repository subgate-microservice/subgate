import secrets
from typing import Optional
from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.auth.domain.exceptions import AuthenticationError
from backend.shared.base_models import MyBase
from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.utils.dt import get_current_datetime
from backend.shared.utils.password_helper import PasswordHelper


class InvalidApikeyFormat(ValueError):
    pass


class ApikeyCreate(MyBase):
    title: str
    auth_user: AuthUser
    public_id: str = Field(default_factory=lambda: f"apikey_{uuid4().hex[:8]}")
    secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)


class ApikeyManager:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._password_helper = PasswordHelper()

    async def _check(self, apikey_secret: str) -> Optional[Apikey]:
        try:
            public_id, secret = apikey_secret.split(":")
        except ValueError:
            raise InvalidApikeyFormat()

        try:
            apikey = await self._uow.apikey_repo().get_one_by_public_id(public_id)
            is_valid = self._password_helper.verify(secret, apikey.hashed_secret)
            if is_valid:
                return apikey
        except LookupError:
            return None

    async def create(self, data: ApikeyCreate):
        hashed_secret = self._password_helper.hash(data.secret)

        apikey = Apikey(
            title=data.title,
            auth_user=data.auth_user,
            public_id=data.public_id,
            hashed_secret=hashed_secret,
            created_at=data.created_at,
        )
        await self._uow.apikey_repo().add_one(apikey)

    async def get_by_public_id(self, public_id: str) -> Apikey:
        return await self._uow.apikey_repo().get_one_by_public_id(public_id)

    async def get_by_secret(self, apikey_secret: str) -> Apikey:
        result = await self._check(apikey_secret)
        if not result:
            raise AuthenticationError()
        return result
