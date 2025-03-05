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


async def update_password(username: str, old_pass: str, new_pass: str, session):
    async with get_user_db(session) as user_db:
        async with get_user_manager(user_db) as user_manager:
            user_manager: UserManager
            credentials = OAuth2PasswordRequestForm(grant_type="password", password=old_pass, username=username)
            authenticated = await user_manager.authenticate(credentials)
            if not authenticated:
                raise HTTPException(status_code=400, detail="BAD_CREDENTIALS")
            user_update = UserUpdate(password=new_pass)
            await user_manager.update(user_update, authenticated)


async def update_username(old_username: str, new_username: str, password: str, session):
    async with get_user_db(session) as user_db:
        async with get_user_manager(user_db) as user_manager:
            user_manager: UserManager
            credentials = OAuth2PasswordRequestForm(grant_type="password", password=password, username=old_username)
            authenticated = await user_manager.authenticate(credentials)
            if not authenticated:
                raise HTTPException(status_code=400, detail="BAD_CREDENTIALS")
            user_update = UserUpdate(password=password, email=new_username)
            await user_manager.update(user_update, authenticated)


async def delete_profile(username: str, password: str, session):
    async with get_user_db(session) as user_db:
        async with get_user_manager(user_db) as user_manager:
            user_manager: UserManager
            credentials = OAuth2PasswordRequestForm(grant_type="password", password=password, username=username)
            authenticated = await user_manager.authenticate(credentials)
            if not authenticated:
                raise HTTPException(status_code=400, detail="BAD_CREDENTIALS")
            await user_manager.delete(authenticated)
