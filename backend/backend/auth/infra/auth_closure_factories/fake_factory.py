import functools
import uuid
from typing import Optional, Callable

from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.application.auth_closure_factory import AuthClosureFactory
from backend.auth.domain.auth_user import AuthUser, AuthRole


class FakeAuthClosureFactory(AuthClosureFactory):
    def __init__(
            self,
            data: dict[str, AuthUser] = None,
            always_authenticated=False,
    ):
        self.data = data if data else {}
        self._always_authenticated = AuthUser(id=uuid.uuid4(), roles={AuthRole.Admin}) if always_authenticated else None
        self._bearer_scheme = HTTPBearer(auto_error=False)

    def get_code(self):
        return "fake_factory"

    def fastapi_closure(
            self,
            optional: bool = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> Callable:
        closure = self._bearer_scheme

        @functools.wraps(closure)
        async def dependency(*args, **kwargs) -> Optional[AuthUser]:
            # Ensure we have access to the request context
            request: Request = kwargs.get("request")

            if request is None:
                try:
                    request = args[0]
                except IndexError:
                    raise HTTPException(status_code=400, detail="Request context is missing.")

            credentials: Optional[HTTPAuthorizationCredentials] = await closure(request)

            if self._always_authenticated:
                return self._always_authenticated

            if credentials is None:
                if optional:
                    return None
                raise HTTPException(status_code=401, detail="Authorization token is missing.")

            token = credentials.credentials  # Extract token string
            auth_user = self.data.get(token)
            if not auth_user:
                if optional:
                    return None
                raise HTTPException(status_code=401, detail="Invalid or unauthorized token.")

            return auth_user

        return dependency
