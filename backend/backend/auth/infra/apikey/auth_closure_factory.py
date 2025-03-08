from typing import Optional

from fastapi import Request

from backend.auth.application.apikey_service import ApikeyManager, InvalidApikeyFormat
from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure
from backend.auth.domain.apikey import Apikey
from backend.auth.domain.exceptions import AuthenticationError
from backend.shared.unit_of_work.uow import UnitOfWorkFactory
from backend.shared.utils.cache_manager import CacheManager


class ApikeyAuthClosureFactory(AuthClosureFactory):
    def __init__(
            self,
            uow_factory: UnitOfWorkFactory,
            cache_manager: CacheManager[Apikey],
            cache_time: float,
    ):
        self._uow_factory = uow_factory
        self._cache_manger = cache_manager
        self._cache_time = cache_time

    def get_code(self):
        return "apikey_factory"

    def fastapi_closure(
            self,
            optional: bool = False,
            scope: Optional[list[str]] = None,
            permissions: Optional[list[str]] = None,
    ) -> FastapiAuthClosure:

        async def closure(
                request: Request,
        ):
            apikey_value = request.headers.get("x-api-key")
            if not apikey_value:
                if optional:
                    return None
                raise AuthenticationError("Missing 'X-API-Key' header")

            cached = self._cache_manger.get(apikey_value)
            if cached:
                return cached.auth_user

            async with self._uow_factory.create_uow() as uow:
                manager = ApikeyManager(uow)
                apikey = await manager.get_by_secret(apikey_value)
                self._cache_manger.set(apikey_value, apikey, self._cache_time)
                return apikey.auth_user

        return closure
