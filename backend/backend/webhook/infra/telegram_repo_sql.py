from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Column, String, Table, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import UUID, Integer, BigInteger

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SQLMapper, AwareDateTime
from backend.shared.utils import get_current_datetime
from backend.webhook.domain.telegram import Telegram, TelegramRepo

telegram_table = Table(
    "telegram",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("url", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("status", String, nullable=False),
    Column("retries", Integer, nullable=False),
    Column("max_retries", Integer, nullable=False),
    Column("error_info", JSONB, nullable=True),
    Column("sent_at", AwareDateTime(timezone=True), nullable=False),
    Column("next_retry_at", AwareDateTime(timezone=True), nullable=True),
    Column("created_at", AwareDateTime(timezone=True), nullable=False),
    Column("updated_at", AwareDateTime(timezone=True), nullable=False),
    Column("partkey", UUID, nullable=False),
)


class SqlTelegramMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Telegram

    def entity_to_mapping(self, entity: Telegram) -> dict:
        result = entity.model_dump(mode="json")
        if result["id"] == -1:
            result.pop("id")
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

    def sby_to_filter(self, sby):
        raise NotImplemented


class SqlTelegramRepo(TelegramRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._session = session
        self._mapper = SqlTelegramMapper(telegram_table)
        self._transaction_id = transaction_id

    async def get_all(self, lock: Lock = "write") -> list[Telegram]:
        stmt = (
            telegram_table
            .select()
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        records = result.mappings()
        return [self._mapper.mapping_to_entity(x) for x in records]

    async def get_messages_for_send(self, limit=500, lock: Lock = "write") -> list[Telegram]:
        stmt = (
            telegram_table
            .select()
            .with_for_update()
            .where(
                telegram_table.c["next_retry_at"] <= get_current_datetime(),
                telegram_table.c["next_retry_at"].isnot(None),
            )
            .limit(limit)
            .order_by(telegram_table.c["id"])
        )
        result = await self._session.execute(stmt)
        records = result.mappings()
        return [self._mapper.mapping_to_entity(x) for x in records]

    async def add_one(self, item: Telegram) -> None:
        stmt = telegram_table.insert()
        data = self._mapper.entity_to_mapping(item)
        await self._session.execute(stmt, data)

    async def add_many(self, items: Iterable[Telegram]) -> None:
        if items:
            stmt = telegram_table.insert()
            data = [self._mapper.entity_to_mapping(item) for item in items]
            await self._session.execute(stmt, data)

    async def update_one(self, item: Telegram) -> None:
        stmt = (
            telegram_table
            .update()
            .where(telegram_table.c["id"] == item.id)
        )
        data = self._mapper.entity_to_mapping(item)
        await self._session.execute(stmt, data)

    async def update_many(self, items: Iterable[Telegram]) -> None:
        if items:
            params = {
                col: col
                for col in self._mapper.entity_to_mapping(next(x for x in items)).keys()
                if col != "id"
            }
            data = [
                self._mapper.entity_to_mapping(x)
                for x in items
            ]
            for mapping in data:
                mapping["_id"] = mapping.pop("id")

            stmt = (
                telegram_table
                .update()
                .where(telegram_table.c["id"] == bindparam("_id"))
                .values(params)
            )
            await self._session.execute(stmt, data)

    async def delete_one(self, item: Telegram) -> None:
        stmt = (
            telegram_table
            .delete()
            .where(telegram_table.c["id"] == item.id)
        )
        await self._session.execute(stmt)

    async def delete_many(self, items: Iterable[Telegram]) -> None:
        if items:
            ids = [x.id for x in items]
            stmt = (
                telegram_table
                .delete()
                .where(telegram_table.c["id"].in_(ids))
            )
            await self._session.execute(stmt)

    def parse_logs(self):
        return []
