import pytest

from backend.bootstrap import get_container
from tests.conftest import session

container = get_container()


class TestUpdatePassword:
    @pytest.mark.asyncio
    async def test_update_password_with_right_credentials(self, session):
        print(session.cookies)
        response = await session.get("/users/me", cookies=session.cookies)
        print(response.status_code)
