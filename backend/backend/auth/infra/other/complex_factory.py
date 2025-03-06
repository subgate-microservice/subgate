import inspect
from typing import Optional

from fastapi import Request

from backend.auth.application.auth_closure_factory import FastapiAuthClosure
from backend.auth.infra.apikey.auth_closure_factory import ApikeyAuthClosureFactory
from backend.auth.infra.fastapi_users.auth_closure_factory import FastapiUsersAuthClosureFactory


def change_signature(new_signature):
    def decorator(func):
        func.__signature__ = new_signature  # Меняем сигнатуру
        return func

    return decorator


class ComplexFactory:
    def __init__(
            self,
            token_factory: FastapiUsersAuthClosureFactory,
            apikey_closure_factory: ApikeyAuthClosureFactory
    ):
        self._apikey_closure_factory = apikey_closure_factory
        self._token_factory = token_factory

    def fastapi_closure(
            self,
            optional: Optional[bool] = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        apikey_auth_closure = self._apikey_closure_factory.fastapi_closure(optional, scope, permissions)
        token_auth_closure = self._token_factory.fastapi_closure(optional, scope, permissions)

        sig = inspect.signature(token_auth_closure)

        params = list(sig.parameters.values())
        params = [
                     inspect.Parameter(
                         name="request",
                         kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                         annotation=Request
                     )
                 ] + params

        # Создаём новую сигнатуру
        new_sig = sig.replace(parameters=params)

        @change_signature(new_sig)
        async def closure(request: Request, *args, **kwargs):
            apikey = request.headers.get("x-api-key")
            if apikey:
                return await apikey_auth_closure(request)
            else:
                return await token_auth_closure(*args, **kwargs)

        return closure
