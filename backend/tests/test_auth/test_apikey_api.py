import pytest

from backend.auth.adapters.apikey_router import ApikeyCreate
from backend.auth.application.apikey_service import ApikeyManager
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from tests.conftest import client, current_user

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
