import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient as HttpAsyncClient
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine

from backend import config
from backend.auth.application.apikey_service import ApikeyCreate, ApikeyManager
from backend.auth.application.auth_usecases import AuthUserCreate
from backend.bootstrap import get_container
from backend.main import app
from backend.shared.utils.dt import get_current_datetime
from backend.startup_service import StartupShutdownManager
from backend.subscription.domain.plan_repo import PlanSby
from backend.subscription.domain.subscription_repo import SubscriptionSby
from backend.webhook.domain.webhook_repo import WebhookSby

container = get_container()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Создаёт общий event loop для всех тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def fake_postgres_database():
    user, password, host, port, name = config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_PORT, config.DB_NAME
    url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}_test"
    return create_async_engine(url, echo=False, future=True)


@pytest.fixture(autouse=True, scope="session")
def override_deps():
    logger.info("Overriding database dependency...")
    container.set_dependency("database", fake_postgres_database())


@pytest_asyncio.fixture(autouse=True, scope="session")
async def preparations():
    db_name = config.DB_NAME + "_test"
    manager = StartupShutdownManager(db_name=db_name)
    await manager.on_startup()

    yield

    await manager.on_shutdown()


@pytest_asyncio.fixture(scope="session", autouse=False)
async def current_user():
    auth_usecase = container.auth_usecase()
    try:
        current_user = await auth_usecase.get_auth_user_by_email("user_for_test@gmaiil.com")
    except Exception:
        auth_create = AuthUserCreate(email="user_for_test@gmaiil.com", password="1234qwerty")
        current_user = await auth_usecase.create_auth_user(auth_create)
    yield current_user


def get_async_client() -> HttpAsyncClient:
    return HttpAsyncClient(app=app, base_url="http://testserver/api/v1", follow_redirects=True)


@pytest_asyncio.fixture(scope="session")
async def client(current_user):
    async with get_async_client() as client:
        url = "/auth/jwt/login"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {
            "grant_type": "password",
            "username": "user_for_test@gmaiil.com",
            "password": "1234qwerty",
        }

        response = await client.post(url, data=data, headers=headers)

        if response.status_code >= 400:
            logger.warning(f"Login was failed: {response.json()}")
        response.raise_for_status()

        token = response.cookies.get('fastapiusersauth')
        if not token:
            raise ValueError

        client.cookies.set('fastapiusersauth', token)

        yield client


@pytest_asyncio.fixture(scope="session")
async def apikey_client(current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        apikey_create = ApikeyCreate(title="AnyTitle", auth_user=current_user)
        manager = ApikeyManager(uow)
        await manager.create(apikey_create)
        await uow.commit()
        logger.info("ApikeyClient was created")

    async with get_async_client() as c:
        c.headers = {"X-API-Key": f"{apikey_create.public_id}:{apikey_create.secret}"}
        yield c


@pytest_asyncio.fixture(autouse=True)
async def clear():
    async with container.unit_of_work_factory().create_uow() as uow:
        targets = await uow.plan_repo().get_selected(PlanSby())
        await uow.plan_repo().delete_many(targets)

        targets = await uow.subscription_repo().get_selected(SubscriptionSby())
        await uow.subscription_repo().delete_many(targets)

        targets = await uow.webhook_repo().get_selected(WebhookSby())
        await uow.webhook_repo().delete_many(targets)

        before_date = get_current_datetime()
        await uow.delivery_task_repo().delete_many_before_date(before_date)

        await uow.commit()
