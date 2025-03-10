from typing import Mapping, Type, Any

from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import UUID

from backend.auth.domain.apikey import Apikey, ApikeySby, ApikeyRepo
from backend.auth.domain.auth_user import AuthUser
from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SQLMapper, AwareDateTime

apikey_table = Table(
    'apikey',
    metadata,
    Column("public_id", String, nullable=False, index=True, primary_key=True),
    Column('title', String, nullable=False),
    Column("auth_id", ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
    Column("hashed_secret", String, nullable=False),
    Column('created_at', AwareDateTime(timezone=True)),
)


class ApikeySqlMapper(SQLMapper):
    def __init__(self):
        super().__init__(table=apikey_table)

    def get_entity_type(self) -> Type[Any]:
        return Apikey

    def entity_to_mapping(self, entity: Apikey) -> dict:
        result = entity.model_dump(mode="json")
        result["created_at"] = entity.created_at
        result["auth_id"] = entity.auth_user.id
        return result

    def mapping_to_entity(self, data: Mapping) -> Apikey:
        auth_user = AuthUser(id=data["auth_id"])
        return Apikey(
            title=data["title"],
            auth_user=auth_user,
            public_id=data["public_id"],
            hashed_secret=data["hashed_secret"],
            created_at=data["created_at"],
        )

    def entity_to_orm_model(self, entity: Apikey):
        raise NotImplemented

    def sby_to_filter(self, sby: ApikeySby):
        result = []
        if sby.auth_ids:
            result.append(apikey_table.c["auth_id"].in_(sby.auth_ids))
        return result


class SqlApikeyRepo(ApikeyRepo):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = ApikeySqlMapper()

    async def add_one(self, item: Apikey):
        data = self._mapper.entity_to_mapping(item)
        stmt = apikey_table.insert()
        await self._session.execute(stmt, data)

    async def get_selected(self, sby: ApikeySby, lock: Lock = "write") -> list[Apikey]:
        filters = self._mapper.sby_to_filter(sby)
        orders = self._mapper.get_orderby(sby.order_by)
        stmt = apikey_table.select().where(*filters).order_by(*orders)
        result = await self._session.execute(stmt)
        return [self._mapper.mapping_to_entity(x) for x in result.mappings()]

    async def get_one_by_public_id(self, public_id: str) -> Apikey:
        stmt = (
            apikey_table
            .select()
            .where(apikey_table.c["public_id"] == public_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        mapping = result.mappings().one_or_none()
        if not mapping:
            raise LookupError(public_id)
        return self._mapper.mapping_to_entity(mapping)

    async def delete_one(self, item: Apikey) -> None:
        stmt = (
            apikey_table
            .delete()
            .where(apikey_table.c["public_id"] == item.public_id)
        )
        await self._session.execute(stmt)
