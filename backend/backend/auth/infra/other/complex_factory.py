import inspect
from typing import Optional, Callable

from fastapi import Request

from backend.auth.application.auth_closure_factory import FastapiAuthClosure
from backend.auth.infra.apikey.auth_closure_factory import ApikeyAuthClosureFactory
from backend.auth.infra.fastapi_users.auth_closure_factory import FastapiUsersAuthClosureFactory


def change_signature(new_signature: inspect.Signature) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.__signature__ = new_signature
        return func

    return decorator


def _modify_signature(func: Callable) -> inspect.Signature:
    sig = inspect.signature(func)
    new_params = [inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request)]
    new_params.extend(sig.parameters.values())
    return sig.replace(parameters=new_params)


class ComplexFactory:
    def __init__(
            self,
            token_factory: FastapiUsersAuthClosureFactory,
            apikey_closure_factory: ApikeyAuthClosureFactory,
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

        new_sig = _modify_signature(token_auth_closure)

        @change_signature(new_sig)
        async def closure(request: Request, *args, **kwargs):
            return await (
                apikey_auth_closure(request) if request.headers.get("x-api-key") else token_auth_closure(*args,
                                                                                                         **kwargs))

        return closure
