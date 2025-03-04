import pytest

from backend import config
from backend.auth.adapters.fastapi_user_routers import PasswordUpdate
from backend.bootstrap import get_container

container = get_container()


class TestUpdatePassword:
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

        # Helper function to attempt login
        async def login(password):
            return await client.post(
                "/auth/jwt/login",
                data={
                    "grant_type": "password",
                    "username": user_email,
                    "password": password,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )

        # Check login with old password
        response = await login(old_password)
        assert response.status_code == 400

        # Check login with new password
        response = await login(new_password)
        assert response.status_code == 204
