import functools
from typing import Optional, Union

from fastapi import Request, HTTPException
from fastapi.openapi.models import Response
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.fief.auth_closure_factory import FiefAuthClosureFactory


class ComplexAuthClosureFactory(AuthClosureFactory):
    def __init__(
            self,
            token_auth_factory: AuthClosureFactory,
            apikey_auth_factory: AuthClosureFactory,
    ):
        self._token_auth_factory = token_auth_factory
        self._apikey_auth_factory = apikey_auth_factory

    def get_code(self):
        if isinstance(self._token_auth_factory, FiefAuthClosureFactory):
            return "complex_factory_with_fief"
        raise NotImplemented

    def fastapi_closure(
            self,
            optional: bool = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        token_auth_closure = self._token_auth_factory.fastapi_closure(optional, scope, permissions)
        apikey_auth_closure = self._apikey_auth_factory.fastapi_closure(optional, scope, permissions)

        @functools.wraps(token_auth_closure)
        async def dependency(
                request: Request,
                response: Response,
                token: Optional[Union[str, HTTPAuthorizationCredentials]],
        ) -> Optional[AuthUser]:
            if request.headers.get("Apikey-Value") and request.headers.get("Authorization"):
                raise HTTPException(
                    status_code=400,
                    detail="Only Apikey-Value or Authorization available in one request",
                )
            # Check for API key in the headers
            apikey_value = request.headers.get("Apikey-Value")
            if apikey_value:
                return await apikey_auth_closure(request, response, token)
            else:
                return await token_auth_closure(request, response, token)

        return dependency
