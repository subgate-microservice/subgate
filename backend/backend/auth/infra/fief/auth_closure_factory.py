import functools
from typing import Optional

from fastapi.security import OAuth2AuthorizationCodeBearer
from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth

from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.fief.mappers import AuthUserMapper


class FiefAuthClosureFactory(AuthClosureFactory):
    def __init__(
            self,
            fief_base_url: str,
            fief_client_id: str,
            fief_client_secret: str,
    ):
        fief = FiefAsync(
            fief_base_url,
            fief_client_id,
            fief_client_secret,
        )

        scheme = OAuth2AuthorizationCodeBearer(
            f"{fief_base_url}/authorize",
            f"{fief_base_url}/api/token",
            scopes={"openid": "openid", "offline_access": "offline_access"},
            auto_error=False,
        )

        self._fief_auth_client = FiefAuth(fief, scheme)

        self._scheme = scheme
        self._mapper = AuthUserMapper()

    def get_code(self):
        return "fief_factory"

    def fastapi_closure(
            self,
            optional: bool = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        auth_closure = self._fief_auth_client.authenticated(optional, scope, None, permissions)

        @functools.wraps(auth_closure)
        async def dependency(*args, **kwargs) -> Optional[AuthUser]:
            access_token_info = await auth_closure(*args, **kwargs)
            if access_token_info:
                user = self._mapper.access_token_to_auth_user(access_token_info)
                return user

        return dependency
