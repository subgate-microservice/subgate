from typing import Iterable, Mapping, Type, Any

from pydantic import AwareDatetime
from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import UUID, Integer, BigInteger

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SQLMapper, AwareDateTime, SqlBaseRepo
from backend.shared.utils.dt import get_current_datetime
from backend.webhook.domain.delivery_task import DeliveryTask, DeliveryTaskRepo

delivery_task_table = Table(
    "delivery_task",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("url", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("status", String, nullable=False),
    Column("retries", Integer, nullable=False),
    Column("max_retries", Integer, nullable=False),
    Column("error_info", JSONB, nullable=True),
    Column("delays", JSONB, nullable=False),
    Column("last_retry_at", AwareDateTime(timezone=True), nullable=True),
    Column("next_retry_at", AwareDateTime(timezone=True), nullable=True, index=True),
    Column("created_at", AwareDateTime(timezone=True), nullable=False, index=True),
    Column("partkey", String, nullable=False),
    Column("auth_id", ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
    Column("_order_col", BigInteger, primary_key=False, autoincrement=True),
)


class SqlDeliveryTaskMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return DeliveryTask

    def entity_to_mapping(self, entity: DeliveryTask) -> dict:
        result = entity.model_dump(mode="json")
        result["id"] = entity.id
        result["auth_id"] = entity.auth_id
        result["last_retry_at"] = entity.last_retry_at
        result["next_retry_at"] = entity.next_retry_at
        result["created_at"] = entity.created_at
        result["max_retries"] = entity.max_retries
        return result

    def mapping_to_entity(self, data: Mapping) -> DeliveryTask:
        return DeliveryTask(
            url=data["url"],
            data=data["data"],
            status=data["status"],
            id=data["id"],
            retries=data["retries"],
            delays=tuple(data["delays"]),
            error_info=data["error_info"],
            created_at=data["created_at"],
            last_retry_at=data["last_retry_at"],
            partkey=data["partkey"],
            auth_id=data["auth_id"],
        )

    def sby_to_filter(self, sby):
        raise NotImplemented


class SqlDeliveryTaskRepo(DeliveryTaskRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._base_repo = SqlBaseRepo(
            session, SqlDeliveryTaskMapper(delivery_task_table), delivery_task_table, transaction_id
        )

    async def get_all(self, lock: Lock = "write") -> list[DeliveryTask]:
        return await self._base_repo.get_all(lock)

    async def add_one(self, item: DeliveryTask) -> None:
        await self._base_repo.add_one(item)

    async def add_many(self, items: Iterable[DeliveryTask]) -> None:
        await self._base_repo.add_many(items)

    async def update_one(self, item: DeliveryTask) -> None:
        await self._base_repo.update_one(item)

    async def update_many(self, items: Iterable[DeliveryTask]) -> None:
        await self._base_repo.update_many(items)

    async def delete_one(self, item: DeliveryTask) -> None:
        await self._base_repo.delete_one(item)

    async def delete_many(self, items: Iterable[DeliveryTask]) -> None:
        await self._base_repo.delete_many(items)

    def parse_logs(self):
        return self._base_repo.parse_logs()

    async def get_deliveries_for_send(self, limit=500, lock: Lock = "write") -> list[DeliveryTask]:
        stmt = (
            delivery_task_table
            .select()
            .with_for_update()
            .where(
                delivery_task_table.c["next_retry_at"] <= get_current_datetime(),
                delivery_task_table.c["next_retry_at"].isnot(None),
                delivery_task_table.c["retries"] < delivery_task_table.c["max_retries"],
            )
            .limit(limit)
            .order_by(delivery_task_table.c["_order_col"])
        )
        result = await self._base_repo.session.execute(stmt)
        records = result.mappings()
        return [self._base_repo.mapper.mapping_to_entity(x) for x in records]

    async def delete_many_before_date(self, dt: AwareDatetime) -> None:
        stmt = (
            delivery_task_table
            .delete()
            .where(delivery_task_table.c["created_at"] < dt)
        )
        await self._base_repo.session.execute(stmt)
