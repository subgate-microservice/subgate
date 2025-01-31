from uuid import uuid4

from async_pymongo import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend import config
from backend.auth.application.auth_closure_factory import AuthClosureFactory
from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.auth.infra.auth_closure_factories.apikey_factory import ApikeyAuthClosureFactory
from backend.auth.infra.auth_closure_factories.fake_factory import FakeAuthClosureFactory
from backend.shared.eventbus import Eventbus
from backend.shared.unit_of_work.uow import UnitOfWorkFactory
from backend.shared.unit_of_work.uow_postgres import SqlUowFactory
from backend.subscription.domain.cycle import Cycle
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription
from backend.subscription.infra.subscription_client import SubscriptionClient, FakeSubscriptionClient
from backend.webhook.application.encrypt_service import GDPRCompliantEncryptor
from backend.webhook.application.telegraph import Telegraph


def create_fake_auth_service():
    auth_user = AuthUser(
        id=AuthId("91a517f0-6d78-4fe9-acaa-ac10fa8f139b"),
    )
    auth_service = FakeAuthClosureFactory({"FakeAuthToken": auth_user})
    return auth_service


def create_fake_subclient():
    plan = Plan(
        title="FakePlan",
        price=100,
        billing_cycle=Cycle(title="Annual", code="Annual", cycle_in_days=365),
        currency="USD",
        level=1,
        auth_id=uuid4(),
    )
    sub = Subscription(
        auth_id=uuid4(),
        subscriber_id="91a517f0-6d78-4fe9-acaa-ac10fa8f139b",
        plan=plan,
    )
    subscription_client = FakeSubscriptionClient({sub.id: sub})
    return subscription_client


class Bootstrap:
    def __init__(self):
        self._eventbus = None
        self._database = None
        self._uow = None
        self._auth_service = None
        self._auth_closure_factory = None
        self._subscription_client = None
        self._encryptor = None
        self._uow_factory = None
        self._telegraph = None

    def set_dependency(self, name: str, value):
        name = "_" + name
        self.__getattribute__(name)
        self.__setattr__(name, value)

    def eventbus(self) -> Eventbus:
        if not self._eventbus:
            self._eventbus = Eventbus()
        return self._eventbus

    def database(self):
        if not self._database:
            _client = AsyncClient(
                host=config.DB_HOST,
                port=config.DB_PORT,
                username=config.DB_USER,
                password=config.DB_PASSWORD,
            )
            self._database = create_async_engine(config.POSTGRES_URL, echo=False, future=True)
        return self._database

    def unit_of_work_factory(self) -> UnitOfWorkFactory:
        if not self._uow_factory:
            if isinstance(self.database(), AsyncEngine):
                self._uow_factory = SqlUowFactory(self.database())
            else:
                raise TypeError(type(self.database()))
        return self._uow_factory

    def auth_closure_factory(self) -> AuthClosureFactory:
        if not self._auth_closure_factory:
            apikey_auth_closure_factory = ApikeyAuthClosureFactory(self.unit_of_work_factory())
            # fief_auth_closure_factory = FiefAuthClosureFactory(
            #     config.FIEF_BASE_URL,
            #     config.FIEF_CLIENT_ID,
            #     config.FIEF_CLIENT_SECRET,
            # )
            # self._auth_closure_factory = ComplexAuthClosureFactory(
            #     fief_auth_closure_factory,
            #     apikey_auth_closure_factory
            # )
            self._auth_closure_factory = apikey_auth_closure_factory
        return self._auth_closure_factory

    def encrypt_service(self) -> GDPRCompliantEncryptor:
        if not self._encryptor:
            self._encryptor = GDPRCompliantEncryptor(config.ENCRYPTOR_PASS)
        return self._encryptor

    def telegraph(self) -> Telegraph:
        if not self._telegraph:
            self._telegraph = Telegraph(self.unit_of_work_factory())
        return self._telegraph

    def subscription_client(self) -> SubscriptionClient:
        if not self._subscription_client:
            self._subscription_client = create_fake_subclient()
        return self._subscription_client


container = Bootstrap()


def get_container():
    return container


auth_closure = get_container().auth_closure_factory().fastapi_closure()
