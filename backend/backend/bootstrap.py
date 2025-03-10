from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker

from backend import config
from backend.auth.application.auth_closure_factory import AuthClosureFactory
from backend.auth.application.auth_usecases import AuthUsecase
from backend.auth.domain.apikey import Apikey
from backend.auth.infra.apikey.auth_closure_factory import ApikeyAuthClosureFactory
from backend.auth.infra.fastapi_users.auth_closure_factory import FastapiUsersAuthClosureFactory
from backend.auth.infra.fastapi_users.manager import create_fastapi_users
from backend.auth.infra.fastapi_users.usecases import FastapiUsersUsecase
from backend.auth.infra.other.complex_factory import ComplexFactory
from backend.shared.event_driven.bus import Bus
from backend.shared.unit_of_work.uow import UnitOfWorkFactory
from backend.shared.unit_of_work.uow_postgres import SqlUowFactory
from backend.shared.utils.cache_manager import CacheManager, InMemoryCacheManager
from backend.shared.utils.worker import Worker
from backend.webhook.application.encrypt_service import GDPRCompliantEncryptor
from backend.webhook.application.telegraph import Telegraph


class Bootstrap:
    def __init__(self):
        self._eventbus = None
        self._database = None
        self._session_factory = None
        self._uow = None
        self._auth_service = None
        self._auth_closure_factory = None
        self._subscription_client = None
        self._encryptor = None
        self._uow_factory = None
        self._telegraph_worker = None
        self._fastapi_users = None
        self._cache_manager = None
        self._auth_token_cache_manager = None

    def set_dependency(self, name: str, value):
        name = "_" + name
        self.__getattribute__(name)
        self.__setattr__(name, value)

    def eventbus(self) -> Bus:
        if not self._eventbus:
            self._eventbus = Bus()
        return self._eventbus

    def database(self):
        if not self._database:
            user, password, host, port, name = config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_PORT, config.DB_NAME
            url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
            self._database = create_async_engine(url, echo=False, future=True)
        return self._database

    def fastapi_users(self):
        if not self._fastapi_users:
            self._fastapi_users = create_fastapi_users(self.session_factory())
        return self._fastapi_users

    def session_factory(self):
        if not self._session_factory:
            self._session_factory = async_sessionmaker(self.database(), expire_on_commit=False)
        return self._session_factory

    def auth_usecase(self) -> AuthUsecase:
        return FastapiUsersUsecase(self.session_factory())

    def unit_of_work_factory(self) -> UnitOfWorkFactory:
        if not self._uow_factory:
            if isinstance(self.database(), AsyncEngine):
                self._uow_factory = SqlUowFactory(self.database())
            else:
                raise TypeError(type(self.database()))
        return self._uow_factory

    def auth_closure_factory(self) -> AuthClosureFactory:
        if not self._auth_closure_factory:
            token_factory = FastapiUsersAuthClosureFactory(self.fastapi_users(), self.auth_token_cache_manager())
            apikey_factory = ApikeyAuthClosureFactory(self.unit_of_work_factory(), self.apikey_cache_manager())
            complex_factory = ComplexFactory(token_factory, apikey_factory)
            self._auth_closure_factory = complex_factory
        return self._auth_closure_factory

    def encrypt_service(self) -> GDPRCompliantEncryptor:
        if not self._encryptor:
            self._encryptor = GDPRCompliantEncryptor(config.ENCRYPTOR_PASS)
        return self._encryptor

    def telegraph_worker(self) -> Worker:
        if not self._telegraph_worker:
            telegraph = Telegraph(self.unit_of_work_factory())
            self._telegraph_worker = Worker(telegraph.notify, sleep_time=10, safe=True, task_name="Telegraph worker")
        return self._telegraph_worker

    def apikey_cache_manager(self) -> CacheManager[Apikey]:
        if not self._cache_manager:
            self._cache_manager = InMemoryCacheManager(config.AUTHENTICATION_CACHE_TIME)
        return self._cache_manager

    def auth_token_cache_manager(self) -> CacheManager[str]:
        if not self._auth_token_cache_manager:
            self._auth_token_cache_manager = InMemoryCacheManager(config.AUTHENTICATION_CACHE_TIME)
        return self._auth_token_cache_manager


container = Bootstrap()


def get_container():
    return container


auth_closure = get_container().auth_closure_factory().fastapi_closure()
