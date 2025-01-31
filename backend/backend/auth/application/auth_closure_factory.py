from abc import ABC, abstractmethod
from typing import Callable, Optional
from typing import Union, Awaitable

from fastapi import Request
from fastapi import Response
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth.domain.auth_user import AuthUser

FastapiAuthClosure = Callable[[Request, Response, Union[str, HTTPAuthorizationCredentials, None,]], Awaitable[AuthUser]]


class AuthClosureFactory(ABC):
    @abstractmethod
    def get_code(self):
        pass

    @abstractmethod
    def fastapi_closure(
            self,
            optional: Optional[bool] = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        raise NotImplemented
