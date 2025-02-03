import inspect
from typing import (
    Optional,
)

from fastapi import Request
from fastapi_users import FastAPIUsers

from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure


class FastapiUsersAuthClosureFactory(AuthClosureFactory):
    def __init__(self, fastapi_users: FastAPIUsers):
        self._fastapi_users = fastapi_users

    def get_code(self):
        return "fastapi_users"

    def fastapi_closure(
            self,
            optional: Optional[bool] = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        auth_closure = self._fastapi_users.current_user(active=True)

        sig = inspect.signature(auth_closure)

        new_param = inspect.Parameter(
            "request",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Request
        )
        new_signature = sig.replace(parameters=[new_param, *sig.parameters.values()])

        # Обновляем сигнатуру функции
        auth_closure.__signature__ = new_signature

        return auth_closure
