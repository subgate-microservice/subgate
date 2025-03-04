import pytest

from backend.bootstrap import get_container
from tests.conftest import client

container = get_container()


class TestUpdatePassword:
    @pytest.mark.asyncio
    async def test_update_password_with_right_credentials(self, client):
        response = await client.get("/users/me")
        response.raise_for_status()
