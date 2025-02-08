from typing import Literal, NamedTuple, Iterable, Any, Self, Optional, cast, Mapping

from pydantic import AwareDatetime, TypeAdapter
from sqlalchemy import Table, Column, UUID, String, DateTime, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database import metadata
from backend.shared.utils import get_current_datetime

Action = Literal[
    "insert",
    "update",
    "delete",
    "safe_delete",
    "rollback_insert",
    "rollback_update",
    "rollback_delete",
    "rollback_safe_delete",
]

adapter = TypeAdapter(Optional[dict])


class Log(NamedTuple):
    transaction_id: UUID
    action: Action
    action_id: UUID
    action_data: Optional[dict[str, Any]]
    rollback_data: Optional[dict[str, Any]]
    collection_name: str
    created_at: AwareDatetime

    def model_copy(self, update: dict = None) -> Self:
        return self._replace(**update)

    @property
    def fields(self):
        return self._fields

    def to_rollback_log(self) -> Self:
        return self._replace(
            action=cast(Action, "rollback_" + self.action),
            action_data=None,
            rollback_data=None,
            created_at=get_current_datetime(),
        )


log_table = Table(
    "log_table",
    metadata,
    Column("pk", BigInteger, autoincrement=True, primary_key=True),
    Column('action', String, nullable=False),
    Column('transaction_id', UUID, nullable=False),
    Column('action_id', UUID),
    Column('action_data', String, nullable=False),
    Column('rollback_data', String, nullable=True),
    Column('collection_name', String, nullable=False),
    Column('created_at', DateTime(timezone=True)), )


class SqlLogMapper:
    @staticmethod
    def entity_to_mapping(entity: Any) -> dict:
        return {
            "action": entity.action,
            "action_id": entity.action_id,
            "action_data": adapter.dump_json(entity.action_data).decode(),
            "rollback_data": adapter.dump_json(entity.rollback_data).decode(),
            "collection_name": entity.collection_name,
            "created_at": entity.created_at,
            "transaction_id": entity.transaction_id,
        }

    @staticmethod
    def mapping_to_entity(mapping: Mapping) -> Any:
        return Log(
            action=mapping["action"],
            action_id=mapping["action_id"],
            action_data=adapter.validate_json(mapping["action_data"]),
            rollback_data=adapter.validate_json(mapping["rollback_data"]),
            collection_name=mapping["collection_name"],
            created_at=mapping["created_at"],
            transaction_id=mapping["transaction_id"],
        )


class SqlLogRepo:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = SqlLogMapper()

    async def add_many_logs(self, logs: Iterable[Log]) -> None:
        if logs:
            data = [self._mapper.entity_to_mapping(log) for log in logs]
            stmt = log_table.insert()
            await self._session.execute(stmt, data)

    async def get_logs_by_transaction_id(self, trs_id: UUID) -> list[Log]:
        stmt = (
            log_table
            .select()
            .where(log_table.c["transaction_id"] == trs_id)
            .order_by(log_table.c["pk"])
        )
        mappings = (await self._session.execute(stmt)).mappings()
        logs = [self._mapper.mapping_to_entity(mapping) for mapping in mappings]
        return logs
