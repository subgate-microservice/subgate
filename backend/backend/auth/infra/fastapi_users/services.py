import contextlib
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from backend.auth.infra.fastapi_users.database import User
from backend.auth.infra.fastapi_users.manager import UserManager
from backend.auth.infra.fastapi_users.schemas import UserUpdate


@contextlib.asynccontextmanager
async def get_user_db(session):
    yield SQLAlchemyUserDatabase(session, User)


@contextlib.asynccontextmanager
async def get_user_manager(user_db: SQLAlchemyUserDatabase):
    yield UserManager(user_db)


class FastapiusersUserService:
    def __init__(self, session):
        self.session = session

    async def _get_user_manager(self) -> UserManager:
        async with get_user_db(self.session) as user_db:
            async with get_user_manager(user_db) as user_manager:
                return user_manager

    async def _authenticate(self, username: str, password: str) -> User:
        user_manager = await self._get_user_manager()
        credentials = OAuth2PasswordRequestForm(grant_type="password", password=password, username=username)
        user = await user_manager.authenticate(credentials)
        if not user:
            raise HTTPException(status_code=400, detail="BAD_CREDENTIALS")
        return user

    async def update_password(self, username: str, old_pass: str, new_pass: str):
        user = await self._authenticate(username, old_pass)
        user_manager = await self._get_user_manager()
        await user_manager.update(UserUpdate(password=new_pass), user)

    async def update_username(self, old_username: str, new_username: str, password: str):
        user = await self._authenticate(old_username, password)
        user_manager = await self._get_user_manager()
        await user_manager.update(UserUpdate(password=password, email=new_username), user)

    async def delete_profile(self, username: str, password: str):
        user = await self._authenticate(username, password)
        user_manager = await self._get_user_manager()
        await user_manager.delete(user)
