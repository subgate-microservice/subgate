from typing import Any, Mapping, Type

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Table, Column, UUID, String, Boolean
from sqlalchemy.orm import registry

from backend.auth.domain.auth_user import AuthUser
from backend.shared.base_models import BaseSby
from backend.shared.unit_of_work.base_repo_sql import SQLMapper
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
    pass


class AuthUserMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return AuthUser

    def entity_to_mapping(self, entity: Any) -> dict:
        raise NotImplemented

    def mapping_to_entity(self, mapping: Mapping) -> Any:
        return AuthUser(
            id=mapping["id"],
        )

    def sby_to_filter(self, sby: BaseSby) -> Any:
        raise NotImplemented
