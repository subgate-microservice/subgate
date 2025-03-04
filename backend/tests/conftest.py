import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient as HttpAsyncClient
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine

from backend import config
from backend.auth.domain.auth_user import AuthUser, AuthRole
from backend.bootstrap import get_container
from backend.main import app
from backend.shared.database import drop_and_create_postgres_tables
from backend.shared.unit_of_work.uow_postgres import SqlUowFactory
from backend.startup_service import run_preparations
from backend.subscription.domain.plan_repo import PlanSby
from backend.subscription.domain.subscription_repo import SubscriptionSby
from backend.webhook.domain.webhook_repo import WebhookSby

admin_user = AuthUser(id=uuid4(), roles={AuthRole.Admin})
paid_user = AuthUser(id=uuid4())
unpaid_user = AuthUser(id=uuid4())

container = get_container()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Создаёт общий event loop для всех тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def fake_postgres_database():
    return create_async_engine(config.POSTGRES_URL, echo=False, future=True)


@pytest.fixture(autouse=True, scope="session")
def override_deps():
    logger.info("Overriding dependencies...")
    container.set_dependency("database", fake_postgres_database())


def get_async_client() -> HttpAsyncClient:
    return HttpAsyncClient(app=app, base_url="http://testserver/api/v1", follow_redirects=True)


@pytest_asyncio.fixture(autouse=True, scope="session")
async def preparations():
    uow_factory = container.unit_of_work_factory()
    if isinstance(uow_factory, SqlUowFactory):
        await drop_and_create_postgres_tables()
    else:
        raise TypeError
    logger.info("Test database was dropped")
    await run_preparations()
    yield


@pytest_asyncio.fixture(scope="session")
async def current_user():
    async with container.unit_of_work_factory().create_uow() as uow:
        auth_user = await uow.auth_user_repo().get_one_by_username(config.USER_EMAIL)
    yield auth_user


@pytest_asyncio.fixture(scope="session")
async def client():
    async with get_async_client() as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def login(client):
    url = "/auth/jwt/login"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {
        "grant_type": "password",
        "username": config.USER_EMAIL,
        "password": config.USER_PASSWORD,
    }

    response = await client.post(url, data=data, headers=headers)
    response.raise_for_status()
    token = response.cookies.get('fastapiusersauth')
    if not token:
        raise ValueError

    client.cookies.set('fastapiusersauth', token)
    yield


@pytest_asyncio.fixture(autouse=True)
async def clear():
    async with container.unit_of_work_factory().create_uow() as uow:
        targets = await uow.plan_repo().get_selected(PlanSby())
        await uow.plan_repo().delete_many(targets)

        targets = await uow.subscription_repo().get_selected(SubscriptionSby())
        await uow.subscription_repo().delete_many(targets)

        targets = await uow.webhook_repo().get_selected(WebhookSby())
        await uow.webhook_repo().delete_many(targets)

        await uow.commit()
