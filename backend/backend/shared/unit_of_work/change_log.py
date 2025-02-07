from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Literal, NamedTuple, Iterable

import orjson
from pydantic import AwareDatetime
from sqlalchemy import Table, Column, UUID, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database import metadata

Action = Literal[
    "insert",
    "insert_many",
    "update",
    "update_many",
    "delete",
    "delete_many",
    "safe_delete",
    "safe_delete_many",
]
Status = Literal[
    "uncommitted",
    "committed",
    "reverted",
    "commit_error",
    "revert_error",
]


class Log[A, R](NamedTuple):
    id: UUID
    action: Action
    action_data: A
    rollback_data: R
    collection_name: str
    status: Status
    created_at: AwareDatetime

    def model_copy(self, update: dict = None):
        return self._replace(**update)

    @property
    def fields(self):
        return self._fields


class ChangeLog:
    def __init__(self):
        self._logs: OrderedDict[UUID, Log] = OrderedDict()

    def append(self, item: Log) -> None:
        self._logs[item.id] = item

    def change_status(self, entry_id: UUID, new_status: Status) -> None:
        self._logs[entry_id] = self._logs[entry_id].model_copy({"status": new_status})

    def get_all(self) -> list[Log]:
        return list(self._logs.values())

    def get_uncommitted(self) -> list[Log]:
        return [x for x in self._logs.values() if x.status == "uncommitted"]

    def get_committed(self) -> list[Log]:
        return [x for x in self._logs.values() if x.status == "committed"]

    def get_reverted(self) -> list[Log]:
        return [x for x in self._logs.values() if x.status == "reverted"]

    def clear_all(self) -> None:
        self._logs.clear()


class LogRepo(ABC):
    @abstractmethod
    def add_many(self, logs: Iterable[Log]):
        pass

    @abstractmethod
    async def update_status(self, ids: Iterable[UUID], new_status: Status) -> None:
        pass


log_table = Table(
    "log_table",
    metadata,
    Column('id', UUID, primary_key=True),
    Column('action', String, nullable=False),
    Column('action_data', String, nullable=False),
    Column('rollback_data', String, nullable=True),
    Column('collection_name', String, nullable=False),
    Column('status', String, nullable=False),
    Column('created_at', DateTime(timezone=True)), )


def log_to_dict(entity: Log) -> dict:
    return {
        "id": entity.id,
        "action": entity.action,
        "action_data": orjson.dumps(entity.action_data).decode(),
        "rollback_data": orjson.dumps(entity.rollback_data).decode(),
        "collection_name": entity.collection_name,
        "status": entity.status,
        "created_at": entity.created_at,
    }


class SqlLogRepo(LogRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_many(self, logs: Iterable[Log]) -> None:
        data = [log_to_dict(log) for log in logs]
        stmt = log_table.insert()
        await self._session.execute(stmt, data)

    async def update_status(self, ids: Iterable[UUID], new_status: Status) -> None:
        stmt = log_table.update().where(log_table.c["id"].in_(ids))
        data = {"status": new_status}
        await self._session.execute(stmt, data)
