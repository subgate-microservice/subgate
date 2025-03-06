import inspect
from inspect import Signature, Parameter
from typing import Optional, cast, Callable

from fastapi import Request, Depends
from fastapi.openapi.models import Response
from fastapi.security.base import SecurityBase

from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.apikey.auth_closure_factory import ApikeyAuthClosureFactory
from backend.auth.infra.fastapi_users.auth_closure_factory import FastapiUsersAuthClosureFactory


class ComplexAuthClosureFactory(AuthClosureFactory):
    def __init__(
            self,
            token_auth_factory: AuthClosureFactory,
            apikey_auth_factory: AuthClosureFactory,
    ):
        self._token_auth_factory = token_auth_factory
        self._apikey_auth_factory = apikey_auth_factory

    def get_code(self):
        raise NotImplemented

    def fastapi_closure(
            self,
            optional: bool = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        token_auth_closure = self._token_auth_factory.fastapi_closure(optional, scope, permissions)
        apikey_auth_closure = self._apikey_auth_factory.fastapi_closure(optional, scope, permissions)

        async def dependency(request: Request) -> Optional[AuthUser]:
            apikey = request.headers.get("x-api-key")
            if apikey:
                return await apikey_auth_closure(request)
            return await token_auth_closure(request)

        return dependency

    @staticmethod
    def _get_signature(scheme: SecurityBase) -> Signature:
        parameters: list[Parameter] = [
            Parameter(
                name="request",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Request,
            ),
            Parameter(
                name="response",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Response,
            ),
            Parameter(
                name="token",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(cast(Callable, scheme)),
            ),
        ]

        return Signature(parameters)


def change_signature(new_signature):
    def decorator(func):
        func.__signature__ = new_signature  # Меняем сигнатуру
        return func

    return decorator


class FooFactory:
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
