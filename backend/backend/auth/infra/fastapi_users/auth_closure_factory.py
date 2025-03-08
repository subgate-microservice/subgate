import functools
from typing import (
    Optional,
)

from fastapi_users import FastAPIUsers

from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure
from backend.shared.utils.cache_manager import CacheManager


class FastapiUsersAuthClosureFactory(AuthClosureFactory):
    def __init__(self, fastapi_users: FastAPIUsers, cache_manger: CacheManager, cache_time: float):
        self._fastapi_users = fastapi_users
        self._cache_manager = cache_manger
        self._cache_time = cache_time

    def get_code(self):
        return "fastapi_users"

    def fastapi_closure(
            self,
            optional: Optional[bool] = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:
        auth_closure = self._fastapi_users.current_user(active=True)

        @functools.wraps(auth_closure)
        async def dependency(*args, **kwargs):
            token = kwargs["jwt"]

            cached = self._cache_manager.get(token)
            if cached:
                return cached

            result = await auth_closure(*args, **kwargs)
            self._cache_manager.set(token, result, self._cache_time)
            return result

        return dependency
