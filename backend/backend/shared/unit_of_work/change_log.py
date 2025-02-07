from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Literal, NamedTuple, Iterable

from pydantic import AwareDatetime

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
    id: str
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
        self._logs: OrderedDict[str, Log] = OrderedDict()

    def append(self, item: Log) -> None:
        self._logs[item.id] = item

    def change_status(self, entry_id: str, new_status: Status) -> None:
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
