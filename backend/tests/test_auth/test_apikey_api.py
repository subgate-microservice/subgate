import pytest
import pytest_asyncio
from loguru import logger

from backend.auth.adapters.apikey_router import ApikeyCreate
from backend.auth.application.apikey_service import ApikeyManager
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from tests.conftest import client, current_user, get_async_client

container = get_container()


@pytest.mark.asyncio
async def test_create_one(current_user, client):
    data = ApikeyCreate(title="My apikey title", auth_user=AuthUser(id=current_user.id)).model_dump(mode="json")
    response = await client.post("/apikey", json=data)
    response.raise_for_status()


@pytest.mark.asyncio
async def test_get_selected(client, current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        for i in range(11):
            item = ApikeyCreate(title="My apikey title", auth_user=AuthUser(id=current_user.id))
            manager = ApikeyManager(uow)
            await manager.create(item)
        await uow.commit()

    # Test
    response = await client.get(f"/apikey")
    response.raise_for_status()


@pytest.mark.asyncio
async def test_delete_one(client, current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        item = ApikeyCreate(title="My apikey title", auth_user=AuthUser(id=current_user.id))
        manager = ApikeyManager(uow)
        await manager.create(item)
        await uow.commit()

    # Test
    response = await client.delete(f"/apikey/{item.id}")
    response.raise_for_status()


class TestCacheWithApikeyApi:

    @pytest_asyncio.fixture(scope="function")
    async def apikey(self, current_user):
        async with container.unit_of_work_factory().create_uow() as uow:
            apikey_create = ApikeyCreate(title="AnyTitle", auth_user=current_user)
            manager = ApikeyManager(uow)
            await manager.create(apikey_create)
            await uow.commit()
            logger.info("Apikey was created")

        yield apikey_create

    @pytest_asyncio.fixture(scope="function")
    async def apikey_client(self, current_user, apikey):
        async with get_async_client() as c:
            c.headers = {"X-API-Key": f"{apikey.public_id}:{apikey.secret}"}
            yield c

    @pytest.mark.asyncio
    async def test_cache_is_clear_after_delete_apikey(self, current_user, apikey_client, apikey):
        response = await apikey_client.get("/users/me")
        response.raise_for_status()

        response = await apikey_client.delete(f"/apikey/{apikey.id}")
        response.raise_for_status()

        response = await apikey_client.get("/users/me")
        assert response.status_code == 400
