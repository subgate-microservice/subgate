from uuid import uuid4

import pytest

from backend.auth.adapters.apikey_router import ApikeyCreate
from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from tests.conftest import current_user, get_async_client

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
async def test_create_one(current_user):
    user, token, expected_status_code = current_user
    data = ApikeyCreate(title="My apikey title").model_dump(mode="json")
    headers = {"Authorization": f"Bearer {token}"}
    async with get_async_client() as client:
        response = await client.post("/apikey", json=data, headers=headers)
        assert response.status_code == get_expected_status(token)


@pytest.mark.asyncio
async def test_get_auth_user_by_apikey_value(current_user):
    user, token, expected_status_code = current_user

    async with container.unit_of_work_factory().create_uow() as uow:
        data = []
        for i in range(11):
            item = create_apikey(user)
            data.append(item)
            await uow.apikey_repo().add_one(item)
        await uow.commit()

    # Test
    async with get_async_client() as client:
        headers = {"Apikey": data[4].value}
        response = await client.get(f"/apikey/get-auth-user", headers=headers)
        assert response.status_code == get_expected_status(token)


@pytest.mark.asyncio
async def test_get_selected(current_user):
    user, token, expected_status_code = current_user

    async with container.unit_of_work_factory().create_uow() as uow:
        data = []
        for i in range(11):
            item = create_apikey(user)
            data.append(item)
            await uow.apikey_repo().add_one(item)
        await uow.commit()

    # Test
    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/apikey", headers=headers)
        assert response.status_code == get_expected_status(token)


@pytest.mark.asyncio
async def test_delete_one(current_user):
    user, token, expected_status_code = current_user
    item = create_apikey(user)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.apikey_repo().add_one(item)
        await uow.commit()

    # Test
    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.delete(f"/apikey/{item.id}", headers=headers)
        assert response.status_code == get_expected_status(token)
