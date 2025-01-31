from typing import Union, Callable, Iterable, Self

from sqlalchemy import Table, Insert, Update, bindparam

from backend.auth.infra.repositories.apikey_repo_sql import apikey_table
from backend.shared.unit_of_work.change_log import Log
from backend.shared.utils import get_current_datetime
from backend.subscription.infra.plan_repo_sql import plan_table
from backend.subscription.infra.subscription_repo_sql import subscription_table
from backend.webhook.infra.telegram_repo_sql import telegram_table
from backend.webhook.infra.webhook_repo_sql import webhook_table


def get_table(tablename: str) -> Table:
    if tablename == plan_table.name:
        return plan_table
    if tablename == webhook_table.name:
        return webhook_table
    if tablename == subscription_table.name:
        return subscription_table
    if tablename == telegram_table.name:
        return telegram_table
    if tablename == apikey_table.name:
        return apikey_table
    raise ValueError(tablename)


Statement = tuple[Union[Insert, Update], Union[list, dict]]


def build_filter_conditions(logs: list[Log], data_key: str):
    table = get_table(logs[0].collection_name)
    filter_by = {}
    for log in logs:
        for key, value in getattr(log, data_key).items():
            filter_by.setdefault(key, []).append(value)
    return [table.c[col].in_(values) for col, values in filter_by.items()]


class SqlStatementBuilder:
    def __init__(self):
        self._logs: list[Log] = []
        self._statements: list[Statement] = []
        self._grouped_logs: dict = {}

        self._action_handlers = {
            "insert": self._handle_insert,
            "update": self._handle_update,
            "safe_delete": self._handle_safe_delete,
        }
        self._rollback_handlers = {
            "insert": self._handle_insert_rollback,
            "update": self._handle_update_rollback,
            "safe_delete": self._handle_safe_delete_rollback,
        }

    def load_logs(self, logs: Iterable[Log]) -> Self:
        self._reset()
        self._logs.extend(logs)
        return self

    def _group_logs(self):
        for log in self._logs:
            self._grouped_logs.setdefault(log.collection_name, {}).setdefault(log.action, []).append(log)

    def _get_action_handler(self, action: str) -> Callable[[str, list[Log]], None]:
        return self._action_handlers[action]

    def _get_rollback_handler(self, action: str) -> Callable[[str, list[Log]], None]:
        return self._rollback_handlers[action]

    def _handle_insert(self, tablename: str, logs: list[Log]):
        if logs:
            stmt = get_table(tablename).insert()
            data = [log.action_data for log in logs]
            self._statements.append((stmt, data))

    def _handle_update(self, tablename: str, logs: list[Log]):
        if logs:
            table = get_table(tablename)
            params = {col: col for col in logs[0].action_data.keys() if col != "id"}

            values = [
                {**log.action_data, "_id": log.action_data.get("id")}
                for log in logs
            ]

            stmt = table.update().where(table.c["id"] == bindparam("_id")).values(params)
            self._statements.append((stmt, values))

    def _handle_safe_delete(self, tablename: str, logs: list[Log]):
        if logs:
            table = get_table(tablename)
            filter_conditions = build_filter_conditions(logs, "action_data")
            stmt = table.update().where(*filter_conditions)
            self._statements.append((stmt, {"_was_deleted": get_current_datetime()}))

    def _handle_insert_rollback(self, tablename: str, logs: list[Log]):
        if logs:
            table = get_table(tablename)
            ids = [log.action_data["id"] for log in logs]
            stmt = table.update().where(table.c["id"].in_(ids))
            self._statements.append((stmt, {"_was_deleted": get_current_datetime()}))

    def _handle_update_rollback(self, tablename: str, logs: list[Log]):
        if logs:
            table = get_table(tablename)
            params = {col: col for col in logs[0].rollback_data.keys() if col != "id"}

            values = [
                {**log.rollback_data, "_id": log.rollback_data.get("id")}
                for log in logs
            ]

            stmt = table.update().where(table.c["id"] == bindparam("_id")).values(params)
            self._statements.append((stmt, values))

    def _handle_safe_delete_rollback(self, tablename: str, logs: list[Log]):
        if logs:
            table = get_table(tablename)
            filter_conditions = build_filter_conditions(logs, "rollback_data")
            stmt = table.update().where(*filter_conditions)
            self._statements.append((stmt, {"_was_deleted": None}))

    def _process_logs(self, handler_resolver: Callable[[str], Callable[[str, list[Log]], None]]):
        self._group_logs()
        for collection_name, actions in self._grouped_logs.items():
            for action, logs in actions.items():
                handler = handler_resolver(action)
                if handler:
                    handler(collection_name, logs)

    def parse_action_statements(self) -> list[Statement]:
        self._process_logs(self._get_action_handler)
        statements = self._statements
        self._reset()
        return statements

    def parse_rollback_statements(self) -> list[Statement]:
        self._process_logs(self._get_rollback_handler)
        statements = self._statements
        self._reset()
        return statements

    def _reset(self):
        self._logs = []
        self._statements = []
        self._grouped_logs = {}
