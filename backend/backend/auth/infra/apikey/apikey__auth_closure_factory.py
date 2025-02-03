from typing import Optional

from fastapi import Request

from backend.auth.application.auth_closure_factory import AuthClosureFactory, FastapiAuthClosure
from backend.shared.unit_of_work.uow import UnitOfWorkFactory


class NotAuthenticated(Exception):
    pass


class ApikeyAuthClosureFactory(AuthClosureFactory):
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

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
                *_args,
                **_kwargs,
        ):
            apikey_value = request.headers.get("Apikey-Value")
            if not apikey_value:
                if optional:
                    return None
                raise NotAuthenticated("Missing 'Apikey-Value' header")
            async with self._uow_factory.create_uow() as uow:
                apikey = await uow.apikey_repo().get_apikey_by_value(apikey_value)
                return apikey.auth_user

        return closure
