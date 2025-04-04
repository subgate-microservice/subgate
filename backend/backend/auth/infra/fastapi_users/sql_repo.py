from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Table, Column, UUID, String, Boolean
from sqlalchemy.orm import registry

from backend.auth.domain.auth_user import AuthUser
from backend.shared.database import metadata

auth_user_table = Table(
    "user",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("email", String, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, nullable=False),
    Column("is_superuser", Boolean, nullable=False),
    Column("is_verified", Boolean, nullable=False),
)

mapper_registry = registry()


@mapper_registry.mapped
class User(SQLAlchemyBaseUserTableUUID):
    def to_auth_user(self) -> AuthUser:
        return AuthUser(id=self.id)
