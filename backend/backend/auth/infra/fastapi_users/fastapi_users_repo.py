from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.auth.application.auth_usecases import AuthUserCreate
from backend.auth.domain.auth_user_repo import AuthUserRepo
from backend.auth.infra.fastapi_users.database import User


class FastapiUsersRepo(AuthUserRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_one_by_id(self, item_id: AuthId) -> AuthUser:
        raise NotImplemented

    async def get_one_by_username(self, username: str) -> AuthUser:
        db = SQLAlchemyUserDatabase(self._session, User)
        user_read = await db.get_by_email(username)
        return AuthUser(id=user_read.id)

    async def add_one(self, item: AuthUserCreate) -> AuthId:
        raise NotImplemented

    async def update_one(self, item: AuthUser) -> None:
        raise NotImplemented

    async def delete_one(self, item: AuthUser) -> None:
        raise NotImplemented

    def parse_logs(self):
        return []
