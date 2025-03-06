import uuid
from typing import Optional, AsyncGenerator

from fastapi import Request, Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    JWTStrategy, CookieTransport,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.auth.infra.fastapi_users.database import User

SECRET = "SECRET"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        pass

    async def on_after_forgot_password(
            self, user: User, token: str, request: Optional[Request] = None
    ):
        pass

    async def on_after_request_verify(
            self, user: User, token: str, request: Optional[Request] = None
    ):
        pass


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


transport = CookieTransport(cookie_max_age=3600)
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=transport,
    get_strategy=get_jwt_strategy,
)


def create_fastapi_users(session_factory: async_sessionmaker[AsyncSession]):
    async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    async def get_user_db(session: AsyncSession = Depends(get_async_session)):
        yield SQLAlchemyUserDatabase(session, User)

    async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
        yield UserManager(user_db)

    fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
    return fastapi_users
