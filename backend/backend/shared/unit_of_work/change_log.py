from collections import defaultdict
from typing import Literal, NamedTuple, Iterable, Any, Self, Optional, cast, Mapping

from pydantic import AwareDatetime, TypeAdapter
from sqlalchemy import Table, Column, UUID, String, DateTime, BigInteger, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database import metadata
from backend.shared.utils.dt import get_current_datetime

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
    model_id: UUID
    model_state: Optional[dict[str, Any]]
    collection_name: str
    created_at: AwareDatetime

    def model_copy(self, update: dict = None) -> Self:
        return self._replace(**update)

    @property
    def fields(self):
        return self._fields


log_table = Table(
    "log_table",
    metadata,
    Column("pk", BigInteger, autoincrement=True, primary_key=True),
    Column('action', String, nullable=False),
    Column('transaction_id', UUID, nullable=False, index=True),
    Column('model_id', UUID, index=True),
    Column('model_state', String, nullable=False),
    Column('collection_name', String, nullable=False, index=True),
    Column('created_at', DateTime(timezone=True), index=True),
)


class SqlLogMapper:
    @staticmethod
    def entity_to_mapping(entity: Log) -> dict:
        return {
            "action": entity.action,
            "model_id": entity.model_id,
            "model_state": adapter.dump_json(entity.model_state).decode(),
            "collection_name": entity.collection_name,
            "created_at": entity.created_at,
            "transaction_id": entity.transaction_id,
        }

    @staticmethod
    def mapping_to_entity(mapping: Mapping) -> Any:
        return Log(
            action=mapping["action"],
            model_id=mapping["model_id"],
            model_state=adapter.validate_json(mapping["model_state"]),
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

    async def delete_old_logs(self, dt: AwareDatetime) -> None:
        stmt = (
            log_table
            .delete()
            .where(log_table.c["created_at"] < dt)
        )
        await self._session.execute(stmt)

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

    async def get_previous_logs(self, model_ids: Iterable[UUID], current_trs_id: UUID) -> list[Log]:
        subquery = (
            select(
                log_table,
                func.row_number()
                .over(partition_by=log_table.c["model_id"], order_by=log_table.c["pk"].desc())
                .label("rn")
            )
            .where(
                log_table.c["model_id"].in_(model_ids),
                log_table.c["transaction_id"] != current_trs_id,
            )
            .subquery()
        )

        stmt = select(subquery).where(subquery.c.rn == 1)

        # Выполнение запроса
        result = await self._session.execute(stmt)
        logs = [self._mapper.mapping_to_entity(x) for x in result.mappings()]
        return logs


Tablename = str
LastState = dict
ModelID = UUID
RollbackTable = dict[Tablename, dict[Action, dict[ModelID, LastState]]]


class LogConverter:
    def __init__(self, current_logs: list[Log], previous_logs: list[Log], transaction_id: UUID):
        self._current_logs = current_logs
        self._previous_logs = {log.model_id: log.model_state for log in previous_logs}
        self._transaction_id = transaction_id

    def _validate_logs(self):
        for log in self._current_logs:
            if log.action.startswith("r"):
                raise ValueError("Current logs should not contain rollback actions.")
            if log.transaction_id != self._transaction_id:
                raise ValueError(f"All logs must have the same transaction_id")

    def _build_rollback_table(self) -> RollbackTable:
        rollback_table = defaultdict(lambda: defaultdict(dict))

        for log in self._current_logs:
            rollback_action = cast(Action, f"rollback_{log.action}")
            last_state = self._previous_logs[log.model_id] if log.action != "insert" else None
            rollback_table[log.collection_name][rollback_action][log.model_id] = last_state

        return rollback_table

    def convert(self) -> list[Log]:
        self._validate_logs()
        rollback_table = self._build_rollback_table()

        return [
            Log(
                transaction_id=self._transaction_id,
                action=rollback_action,
                model_id=model_id,
                model_state=last_state,
                collection_name=tablename,
                created_at=get_current_datetime(),
            )
            for tablename, actions in rollback_table.items()
            for rollback_action, models in actions.items()
            for model_id, last_state in models.items()
        ]
