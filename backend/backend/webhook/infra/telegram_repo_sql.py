import uuid
from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import UUID, Integer, DateTime

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper
from backend.shared.utils import get_current_datetime
from backend.webhook.domain.telegram import Telegram, TelegramRepo

telegram_table = Table(
    "telegram",
    metadata,
    Column("id", UUID, primary_key=True, default=str(uuid.uuid4())),
    Column("url", String, nullable=False),
    Column("data", String, nullable=False),
    Column("status", String, nullable=False),
    Column("retries", Integer, nullable=False),
    Column("max_retries", Integer, nullable=False),
    Column("error_info", JSONB, nullable=True),
    Column("sent_at", DateTime(timezone=True), nullable=False),
    Column("next_retry_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("_was_deleted", DateTime(timezone=True), nullable=True),

)


class SqlTelegramMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Telegram

    def entity_to_mapping(self, entity: Telegram) -> dict:
        result = entity.model_dump(mode="json")
        result["sent_at"] = entity.sent_at
        result["next_retry_at"] = entity.next_retry_at
        result["created_at"] = entity.created_at
        result["updated_at"] = entity.updated_at
        return result

    def mapping_to_entity(self, data: Mapping) -> Telegram:
        return Telegram(
            url=data["url"],
            data=data["data"],
            status=data["status"],
            id=data["id"],
            retries=data["retries"],
            max_retries=data["max_retries"],
            error_info=data["error_info"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            sent_at=data["sent_at"],
            next_retry_at=data["next_retry_at"],
        )

    def entity_to_orm_model(self, entity: Telegram):
        raise NotImplemented

    def sby_to_filter(self, sby):
        raise NotImplemented


class SqlTelegramRepo(TelegramRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._base_repo = SqlBaseRepo(session, SqlTelegramMapper(telegram_table), telegram_table, transaction_id)

    async def create_indexes(self):
        pass

    async def get_all(self, lock: Lock = "write") -> list[Telegram]:
        table = self._base_repo.table
        stmt = (
            table
            .select().with_for_update()
            .where(table.c["_was_deleted"].is_(None))
        )
        result = await self._base_repo.session.execute(stmt)
        records = result.mappings()
        return [self._base_repo.mapper.mapping_to_entity(x) for x in records]

    async def get_messages_for_send(self, limit=500, lock: Lock = "write") -> list[Telegram]:
        table = self._base_repo.table
        stmt = (
            table
            .select()
            # .with_for_update()
            .where(
                table.c["next_retry_at"] < get_current_datetime(),
                table.c["next_retry_at"].isnot(None),
                table.c["_was_deleted"].is_(None),
            )
            .limit(limit)
            .order_by(table.c["created_at"])
        )
        result = await self._base_repo.session.execute(stmt)
        records = result.mappings()
        return [self._base_repo.mapper.mapping_to_entity(x) for x in records]

    async def add_one(self, item: Telegram) -> None:
        await self._base_repo.add_one(item)

    async def add_many(self, items: Iterable[Telegram]) -> None:
        for item in items:
            await self.add_one(item)

    async def update_one(self, item: Telegram) -> None:
        await self._base_repo.update_one(item)

    async def delete_one(self, item: Telegram) -> None:
        await self._base_repo.delete_one(item)

    async def delete_many(self, items: Iterable[Telegram]) -> None:
        for item in items:
            await self.delete_one(item)

    def parse_logs(self):
        return self._base_repo.parse_logs()
