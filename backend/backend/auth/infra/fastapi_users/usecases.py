import contextlib

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from backend.auth.application.auth_usecases import AuthUsecase, AuthUserPasswordUpdate, AuthUserEmailUpdate, \
    AuthUserDelete, AuthUserCreate
from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.auth.infra.fastapi_users.sql_repo import User
from backend.auth.infra.fastapi_users.manager import UserManager
from backend.auth.infra.fastapi_users.schemas import UserUpdate, UserCreate


@contextlib.asynccontextmanager
async def get_user_db(session):
    yield SQLAlchemyUserDatabase(session, User)


@contextlib.asynccontextmanager
async def get_user_manager(user_db: SQLAlchemyUserDatabase):
    yield UserManager(user_db)


class FastapiUsersUsecase(AuthUsecase):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    @contextlib.asynccontextmanager
    async def _get_user_manager(self) -> UserManager:
        async with self.session_factory() as session:
            async with get_user_db(session) as user_db:
                async with get_user_manager(user_db) as user_manager:
                    yield user_manager

    async def _authenticate(self, email: str, password: str) -> User:
        async with self._get_user_manager() as user_manager:
            credentials = OAuth2PasswordRequestForm(grant_type="password", password=password, username=email)
            user = await user_manager.authenticate(credentials)
            if not user:
                raise HTTPException(status_code=400, detail="BAD_CREDENTIALS")
        return user

    async def get_auth_user_by_id(self, id: AuthId) -> AuthUser:
        async with self._get_user_manager() as user_manager:
            target = await user_manager.get(id)
        return AuthUser(id=target.id)

    async def get_auth_user_by_email(self, email: str) -> AuthUser:
        async with self._get_user_manager() as user_manager:
            target = await user_manager.get_by_email(email)
        return AuthUser(id=target.id)

    async def create_auth_user(self, data: AuthUserCreate) -> AuthUser:
        async with self._get_user_manager() as user_manager:
            created = await user_manager.create(UserCreate(email=data.email, password=data.password))
        return AuthUser(id=created.id)

    async def update_password(self, data: AuthUserPasswordUpdate) -> None:
        async with self._get_user_manager() as user_manager:
            target = await user_manager.get(data.id)
            authenticated = await self._authenticate(target.email, data.old_password)

        async with self._get_user_manager() as user_manager:
            await user_manager.update(UserUpdate(password=data.new_password), authenticated)

    async def update_email(self, data: AuthUserEmailUpdate) -> None:
        async with self._get_user_manager() as user_manager:
            target = await user_manager.get(data.id)
            authenticated = await self._authenticate(target.email, data.password)
        async with self._get_user_manager() as user_manager:
            await user_manager.update(UserUpdate(password=data.password, email=data.new_email), authenticated)

    async def delete_auth_user(self, data: AuthUserDelete) -> None:
        async with self._get_user_manager() as user_manager:
            target = await user_manager.get(data.id)
            authenticated = await self._authenticate(target.email, data.password)
        async with self._get_user_manager() as user_manager:
            await user_manager.delete(authenticated)
