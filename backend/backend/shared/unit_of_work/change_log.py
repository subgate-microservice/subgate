from typing import Literal, NamedTuple, Iterable, Any, Self, Optional, cast, Mapping

from pydantic import AwareDatetime, TypeAdapter
from sqlalchemy import Table, Column, UUID, String, DateTime, BigInteger, select, func
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
    Column('transaction_id', UUID, nullable=False),
    Column('model_id', UUID),
    Column('model_state', String, nullable=False),
    Column('collection_name', String, nullable=False),
    Column('created_at', DateTime(timezone=True)), )


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
RollbackAction = Action
LastState = dict
ModelID = UUID
RollbackTable = dict[Tablename, dict[RollbackAction, dict[ModelID, LastState]]]


def _mapping(current_logs: list[Log], previous_logs: list[Log]) -> RollbackTable:
    result: RollbackTable = {}
    last_states: dict[ModelID, LastState] = {log.model_id: log.model_state for log in previous_logs}

    for current_log in current_logs:
        if current_log.action[0] == "r":
            raise ValueError
        model_id = current_log.model_id
        rollback_action = cast(RollbackAction, "rollback_" + current_log.action)
        last_state = last_states[model_id] if current_log.action != "insert" else None
        tablename = current_log.collection_name
        result.setdefault(tablename, {}).setdefault(rollback_action, {})[model_id] = last_state

    return result


def convert_logs(
        current_logs: list[Log],
        previous_logs: list[Log],
        transaction_id: UUID
) -> list[Log]:
    result = []
    rollback_table = _mapping(current_logs, previous_logs)
    for tablename in rollback_table:
        for rollback_action in rollback_table[tablename]:
            for model_id in rollback_table[tablename][rollback_action]:
                last_state = rollback_table[tablename][rollback_action][model_id]
                result.append(
                    Log(
                        transaction_id=transaction_id,
                        action=rollback_action,
                        model_id=model_id,
                        model_state=last_state,
                        collection_name=tablename,
                        created_at=get_current_datetime(),
                    )
                )
    return result
