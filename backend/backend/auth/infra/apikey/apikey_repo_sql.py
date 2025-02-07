import uuid
from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import DateTime, UUID

from backend.auth.domain.apikey import Apikey, ApikeyId
from backend.auth.domain.apikey_repo import ApikeySby, ApikeyRepo
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper
from backend.shared.database import metadata
from backend.shared.unit_of_work.change_log import ChangeLog
from backend.shared.utils import get_current_datetime

apikey_table = Table(
    'apikey',
    metadata,
    Column('id', UUID, primary_key=True, default=str(uuid.uuid4())),
    Column('title', String, nullable=False),
    Column('auth_user', JSONB, nullable=False),
    Column('auth_id', UUID, nullable=False),
    Column('value', String, nullable=False),
    Column('created_at', DateTime(timezone=True), default=get_current_datetime),
    Column('updated_at', DateTime(timezone=True), default=get_current_datetime),
    Column('_was_deleted', DateTime(timezone=True), default=None, nullable=True),
)


class ApikeySqlMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Apikey

    def entity_to_mapping(self, entity: Apikey) -> dict:
        result = entity.model_dump(mode="json")
        result["created_at"] = entity.created_at
        result["updated_at"] = entity.updated_at
        result["auth_id"] = entity.auth_user.id
        return result

    def mapping_to_entity(self, data: Mapping) -> Apikey:
        return Apikey(
            id=str(data["id"]),
            title=data["title"],
            auth_user=data["auth_user"],
            value=data["value"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def entity_to_orm_model(self, entity: Apikey):
        raise NotImplemented

    def sby_to_filter(self, sby: ApikeySby):
        result = []
        if sby.auth_ids:
            result.append(apikey_table.c["auth_id"].in_(sby.auth_ids))
        return result


class SqlApikeyRepo(ApikeyRepo):
    def __init__(self, session: AsyncSession, change_log: ChangeLog):
        self._base_repo = SqlBaseRepo(session, ApikeySqlMapper(apikey_table), apikey_table, change_log)

    async def create_indexes(self):
        pass

    async def add_one(self, item: Apikey) -> None:
        await self._base_repo.add_one(item)

    async def add_many(self, items: Iterable[Apikey]) -> None:
        for item in items:
            await self.add_one(item)

    async def update_one(self, item: Apikey) -> None:
        await self._base_repo.update_one(item)

    async def get_apikey_by_value(self, apikey_value: str, lock: Lock = "write") -> Apikey:
        stmt = (
            apikey_table
            .select()
            .where(
                apikey_table.c["value"] == apikey_value,
                apikey_table.c["_was_deleted"].is_(None),
            )
            .limit(1)
        )
        result = await self._base_repo.session.execute(stmt)
        record = result.mappings().one_or_none()

        if not record:
            raise LookupError(f"AuthUser not exist")

        return self._base_repo.mapper.mapping_to_entity(record)

    async def get_one_by_id(self, item_id: ApikeyId, lock: Lock = "write") -> Apikey:
        return await self._base_repo.get_one_by_id(item_id)

    async def get_selected(self, sby: ApikeySby, lock: Lock = "write") -> list[Apikey]:
        return await self._base_repo.get_selected(sby)

    async def delete_one(self, item: Apikey) -> None:
        await self._base_repo.delete_one(item)

    async def delete_many(self, items: Iterable[Apikey]) -> None:
        for item in items:
            await self.delete_one(item)
