import pytest

from backend import config
from backend.auth.adapters.auth_user_router import PasswordUpdate, EmailUpdate
from backend.bootstrap import get_container

container = get_container()


async def login(username, password, client):
    return await client.post(
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


class TestUpdatePassword:
    @staticmethod
    async def rollback(old_pass, new_pass, client_):
        url = "/users/me/update-password"
        data = PasswordUpdate(old_password=new_pass, new_password=old_pass).model_dump()
        response = await client_.patch(url, json=data)
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_update_password_with_right_credentials(self, client):
        user_email = config.USER_EMAIL
        old_password = config.USER_PASSWORD
        new_password = "hello_world!"

        # Update password
        url = "/users/me/update-password"
        data = PasswordUpdate(old_password=old_password, new_password=new_password).model_dump()
        response = await client.patch(url, json=data)
        response.raise_for_status()

        # Check login with old password
        response = await login(user_email, old_password, client)
        assert response.status_code == 400

        # Check login with new password
        response = await login(user_email, new_password, client)
        assert response.status_code == 204

        # Rollback
        url = "/users/me/update-password"
        data = PasswordUpdate(old_password=new_password, new_password=old_password).model_dump()
        response = await client.patch(url, json=data)
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_update_password_with_wrong_credentials(self, client):
        old_password = "wrong_password"
        new_password = "hello_world!"

        # Update password
        url = "/users/me/update-password"
        data = PasswordUpdate(old_password=old_password, new_password=new_password).model_dump()
        response = await client.patch(url, json=data)
        assert response.status_code == 400


class TestUpdateUsername:
    @pytest.mark.asyncio
    async def test_update_username_with_right_credentials(self, client):
        new_email = "hello_user@gmail.com"
        password = config.USER_PASSWORD

        # Update
        url = "/users/me/update-email"
        data = EmailUpdate(email=new_email, password=password).model_dump()
        response = await client.patch(url, json=data)
        response.raise_for_status()

        response = await login(new_email, password, client)
        assert response.status_code == 204

        # Rollback
        url = "/users/me/update-email"
        data = EmailUpdate(email=config.USER_EMAIL, password=password).model_dump()
        response = await client.patch(url, json=data)
        response.raise_for_status()


class TestDeleteProfile:
    @pytest.mark.asyncio
    async def test_delete_profile(self, client):
        username = config.USER_EMAIL
        password = config.USER_PASSWORD

        url = "/users/me"
        json_data = {"password": password}
        headers = {"Content-Type": "application/json"}

        response = await client.request("DELETE", url, json=json_data, headers=headers)
        response.raise_for_status()

        response = await login(username, password, client)
        assert response.status_code == 400
