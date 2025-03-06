from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Column, String, Table, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import UUID, Integer, BigInteger

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SQLMapper, AwareDateTime
from backend.shared.utils.dt import get_current_datetime
from backend.webhook.domain.delivery_task import DeliveryTask, DeliveryTaskRepo

delivery_task_table = Table(
    "delivery_task",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("url", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("status", String, nullable=False),
    Column("retries", Integer, nullable=False),
    Column("max_retries", Integer, nullable=False),
    Column("error_info", JSONB, nullable=True),
    Column("delays", JSONB, nullable=False),
    Column("last_retry_at", AwareDateTime(timezone=True), nullable=True),
    Column("next_retry_at", AwareDateTime(timezone=True), nullable=True),
    Column("created_at", AwareDateTime(timezone=True), nullable=False),
    Column("partkey", String, nullable=False),
)


class SqlDeliveryTaskMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return DeliveryTask

    def entity_to_mapping(self, entity: DeliveryTask) -> dict:
        result = entity.model_dump(mode="json")
        if result["id"] == -1:
            result.pop("id")
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
        )

    def sby_to_filter(self, sby):
        raise NotImplemented


class SqlDeliveryTaskRepo(DeliveryTaskRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._session = session
        self._mapper = SqlDeliveryTaskMapper(delivery_task_table)
        self._transaction_id = transaction_id

    async def get_all(self, lock: Lock = "write") -> list[DeliveryTask]:
        stmt = (
            delivery_task_table
            .select()
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        records = result.mappings()
        return [self._mapper.mapping_to_entity(x) for x in records]

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
            .order_by(delivery_task_table.c["id"])
        )
        result = await self._session.execute(stmt)
        records = result.mappings()
        return [self._mapper.mapping_to_entity(x) for x in records]

    async def add_one(self, item: DeliveryTask) -> None:
        stmt = delivery_task_table.insert()
        data = self._mapper.entity_to_mapping(item)
        await self._session.execute(stmt, data)

    async def add_many(self, items: Iterable[DeliveryTask]) -> None:
        if items:
            stmt = delivery_task_table.insert()
            data = [self._mapper.entity_to_mapping(item) for item in items]
            await self._session.execute(stmt, data)

    async def update_one(self, item: DeliveryTask) -> None:
        stmt = (
            delivery_task_table
            .update()
            .where(delivery_task_table.c["id"] == item.id)
        )
        data = self._mapper.entity_to_mapping(item)
        await self._session.execute(stmt, data)

    async def update_many(self, items: Iterable[DeliveryTask]) -> None:
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
                delivery_task_table
                .update()
                .where(delivery_task_table.c["id"] == bindparam("_id"))
                .values(params)
            )
            await self._session.execute(stmt, data)

    async def delete_one(self, item: DeliveryTask) -> None:
        stmt = (
            delivery_task_table
            .delete()
            .where(delivery_task_table.c["id"] == item.id)
        )
        await self._session.execute(stmt)

    async def delete_many(self, items: Iterable[DeliveryTask]) -> None:
        if items:
            ids = [x.id for x in items]
            stmt = (
                delivery_task_table
                .delete()
                .where(delivery_task_table.c["id"].in_(ids))
            )
            await self._session.execute(stmt)

    def parse_logs(self):
        return []
