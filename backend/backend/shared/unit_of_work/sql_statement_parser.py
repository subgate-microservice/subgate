from typing import Union, Callable, Iterable, Self, Optional

from sqlalchemy import Table, Insert, Update, bindparam, Delete

from backend.shared.unit_of_work.change_log import Log

Statement = tuple[Union[Insert, Update, Delete], Optional[Union[list, dict]]]


class SqlStatementBuilder:
    def __init__(self, tables: dict[str, Table]):
        self._logs: list[Log] = []
        self._statements: list[Statement] = []
        self._grouped_logs: dict = {}
        self._tables = tables

        self._action_handlers = {
            "insert": self._handle_insert,
            "update": self._handle_update,
            "delete": self._handle_delete,
        }
        self._rollback_handlers = {
            "rollback_insert": self._handle_insert_rollback,
            "rollback_update": self._handle_update_rollback,
            "rollback_delete": self._handle_delete_rollback,
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
            stmt = self._tables[tablename].insert()
            data = [log.model_state for log in logs]
            self._statements.append((stmt, data))

    def _handle_update(self, tablename: str, logs: list[Log]):
        if logs:
            table = self._tables[tablename]
            params = {col: col for col in logs[0].model_state.keys() if col != "id"}

            values = [
                {**log.model_state, "_id": log.model_state.get("id")}
                for log in logs
            ]

            stmt = table.update().where(table.c["id"] == bindparam("_id")).values(params)
            self._statements.append((stmt, values))

    def _handle_delete(self, tablename: str, logs: list[Log]):
        if logs:
            table = self._tables[tablename]
            ids = [log.model_id for log in logs]
            stmt = table.delete().where(table.c["id"].in_(ids))
            self._statements.append((stmt, None))

    def _handle_insert_rollback(self, tablename: str, logs: list[Log]):
        if logs:
            table = self._tables[tablename]
            ids = [log.model_id for log in logs]
            stmt = table.delete().where(table.c["id"].in_(ids))
            self._statements.append((stmt, None))

    def _handle_update_rollback(self, tablename: str, logs: list[Log]):
        if logs:
            table = self._tables[tablename]
            params = {
                col: col
                for col in logs[0].model_state.keys()
                if col != "id"
            }

            data = [
                {**log.model_state, "_id": log.model_id}
                for log in logs
            ]

            stmt = (
                table
                .update()
                .where(table.c["id"] == bindparam("_id"))
                .values(params)
            )
            self._statements.append((stmt, data))

    def _handle_delete_rollback(self, tablename: str, logs: list[Log]):
        if logs:
            table = self._tables[tablename]
            stmt = table.insert()
            data = [x.model_state for x in logs]
            self._statements.append((stmt, data))

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
