import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from async_pymongo import AsyncClient
from httpx import AsyncClient as HttpAsyncClient
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.testclient import TestClient

from backend import config
from backend.auth.application.auth_closure_factory import AuthClosureFactory
from backend.auth.domain.auth_user import AuthUser, AuthRole
from backend.auth.infra.other.fake_factory import FakeAuthClosureFactory
from backend.bootstrap import get_container, auth_closure
from backend.main import app
from backend.shared.permission_service import SubscriptionClient
from backend.shared.unit_of_work.base_repo_sql import drop_and_create_postgres_tables
from backend.shared.unit_of_work.uow_postgres import SqlUowFactory
from backend.startup_service import run_preparations
from backend.subscription.infra.subscription_client import FakeSubscriptionClient
from tests.fake_data import create_subscription

admin_user = AuthUser(id=uuid4(), roles={AuthRole.Admin})
paid_user = AuthUser(id=uuid4())
unpaid_user = AuthUser(id=uuid4())

container = get_container()


@pytest_asyncio.fixture(params=[
    (paid_user, "PaidToken", 200),
    # (unpaid_user, "UnpaidToken", 403),
    # (admin_user, "AdminToken", 200),
])
async def current_user(request) -> tuple[AuthUser, str, int]:
    yield request.param


def fake_mongo_database():
    client = AsyncClient(
        host="127.0.0.1",
        port=config.DB_PORT,
        username=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    return client["my_sub_db_test"]


def fake_postgres_database():
    return create_async_engine(config.POSTGRES_URL, echo=False, future=True)


def fake_auth_closure_factory() -> AuthClosureFactory:
    factory = FakeAuthClosureFactory({
        "AdminToken": admin_user,
        "UnpaidToken": unpaid_user,
        "PaidToken": paid_user,
    })
    return factory


def fake_subscription_client() -> SubscriptionClient:
    sub = create_subscription(subscriber_id=str(paid_user.id))
    return FakeSubscriptionClient({sub.id: sub})


@pytest.fixture(autouse=True, scope="session")
def override_deps():
    logger.info("Overriding dependencies...")
    container.set_dependency("database", fake_postgres_database())
    container.set_dependency("auth_closure_factory", fake_auth_closure_factory())
    container.set_dependency("subscription_client", fake_subscription_client())

    app.dependency_overrides[auth_closure] = container.auth_closure_factory().fastapi_closure()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Создаёт общий event loop для всех тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def preparations():
    await run_preparations()


def get_client() -> TestClient:
    return TestClient(app)


def get_async_client() -> HttpAsyncClient:
    return HttpAsyncClient(app=app, base_url="http://testserver", follow_redirects=True)


@pytest_asyncio.fixture(autouse=True)
async def clear_all():
    uow_factory = container.unit_of_work_factory()
    if isinstance(uow_factory, SqlUowFactory):
        await drop_and_create_postgres_tables()
    else:
        raise TypeError
    logger.info("Test database was dropped")
    yield
