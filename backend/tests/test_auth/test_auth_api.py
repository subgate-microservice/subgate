import pytest
import pytest_asyncio
from fastapi_users.exceptions import UserNotExists

from backend.auth.application.auth_usecases import (
    AuthUserPasswordUpdate, AuthUserEmailUpdate, AuthUserCreate, AuthUserDelete)
from backend.bootstrap import get_container

container = get_container()


async def login(username, password, client):
    response = await client.post(
        "/auth/jwt/login",
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    if response.status_code < 400:
        token = response.cookies.get('fastapiusersauth')
        if not token:
            raise ValueError
        client.cookies.set('fastapiusersauth', token)

    return response


@pytest_asyncio.fixture()
async def user(client):
    auth_create = AuthUserCreate(email="hello@hello.com", password="any_password")
    usecase = container.auth_usecase()
    auth_user = await usecase.create_auth_user(auth_create)
    await login(auth_create.email, auth_create.password, client)

    yield auth_user

    try:
        await login(auth_create.email, auth_create.password, client)
        auth_delete = AuthUserDelete(id=auth_user.id, password=auth_create.password)
        await usecase.delete_auth_user(auth_delete)
    except UserNotExists:
        pass


class TestUpdatePassword:
    @pytest.mark.asyncio
    async def test_update_password_with_right_credentials(self, user, client):
        user_email = "hello@hello.com"
        old_pass = "any_password"
        new_pass = "hello_world!"

        # Update password
        url = "/users/me/update-password"
        data = AuthUserPasswordUpdate(id=user.id, old_password=old_pass, new_password=new_pass).model_dump(mode="json")
        response = await client.patch(url, json=data)
        response.raise_for_status()

        # Check login with old password
        response = await login(user_email, old_pass, client)
        assert response.status_code == 400

        # Check login with new password
        response = await login(user_email, new_pass, client)
        assert response.status_code == 204

        # Rollback password for correct teardown login
        url = "/users/me/update-password"
        data = AuthUserPasswordUpdate(id=user.id, old_password=new_pass, new_password=old_pass).model_dump(mode="json")
        await client.patch(url, json=data)

    @pytest.mark.asyncio
    async def test_update_password_with_wrong_credentials(self, user, client):
        old_password = "wrong_password"
        new_password = "hello_world!"

        # Update password
        url = "/users/me/update-password"
        data = AuthUserPasswordUpdate(
            id=user.id, old_password=old_password, new_password=new_password
        ).model_dump(mode="json")
        response = await client.patch(url, json=data)
        assert response.status_code == 400


class TestUpdateUsername:
    @pytest.mark.asyncio
    async def test_update_username_with_right_credentials(self, user, client):
        new_email = "hello_user@gmail.com"
        password = "any_password"

        # Update
        url = "/users/me/update-email"
        data = AuthUserEmailUpdate(id=user.id, new_email=new_email, password=password).model_dump(mode="json")
        response = await client.patch(url, json=data)
        response.raise_for_status()

        response = await login(new_email, password, client)
        assert response.status_code == 204


class TestDeleteProfile:
    @pytest.mark.asyncio
    async def test_delete_profile(self, user, client):
        username = "hello@hello.com"
        password = "any_password"

        url = "/users/me"
        json_data = {"id": str(user.id), "password": password}
        headers = {"Content-Type": "application/json"}

        response = await client.request("DELETE", url, json=json_data, headers=headers)
        response.raise_for_status()

        response = await login(username, password, client)
        assert response.status_code == 400
