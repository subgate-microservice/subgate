from uuid import uuid4

import pytest

from backend.auth.adapters.apikey_router import ApikeyCreate
from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from tests.conftest import client, current_user

container = get_container()


def create_apikey(auth_user: AuthUser = None):
    if auth_user is None:
        auth_user = AuthUser(id=uuid4())
    return Apikey(
        title=f"Title_{uuid4()}",
        auth_user=auth_user,
    )


def get_expected_status(token: str):
    if token == "AdminToken":
        return 200
    if token == "PaidToken":
        return 200
    if token == "UnpaidToken":
        return 200


@pytest.mark.asyncio
async def test_create_one(client):
    data = ApikeyCreate(title="My apikey title").model_dump(mode="json")
    response = await client.post("/apikey", json=data)
    response.raise_for_status()


@pytest.mark.asyncio
async def test_get_auth_user_by_apikey_value(client, current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        data = []
        for i in range(11):
            item = create_apikey(current_user)
            data.append(item)
            await uow.apikey_repo().add_one(item)
        await uow.commit()

    # Test
    headers = {"Apikey": data[4].value}
    response = await client.get(f"/apikey/get-auth-user", headers=headers)
    response.raise_for_status()


@pytest.mark.asyncio
async def test_get_selected(client, current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        data = []
        for i in range(11):
            item = create_apikey(current_user)
            data.append(item)
            await uow.apikey_repo().add_one(item)
        await uow.commit()

    # Test
    response = await client.get(f"/apikey")
    response.raise_for_status()


@pytest.mark.asyncio
async def test_delete_one(client, current_user):
    item = create_apikey(current_user)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.apikey_repo().add_one(item)
        await uow.commit()

    # Test
    response = await client.delete(f"/apikey/{item.id}")
    response.raise_for_status()
