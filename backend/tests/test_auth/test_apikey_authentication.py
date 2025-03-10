import pytest
import pytest_asyncio
from fastapi import Header, HTTPException
from loguru import logger

from backend.auth.application.apikey_service import ApikeyManager, ApikeyCreate
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container, auth_closure
from backend.main import app
from tests.conftest import get_async_client
from tests.fakes import plan_payload

container = get_container()


@pytest_asyncio.fixture()
async def apikey_secret(current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        apikey_manager = ApikeyManager(uow)
        data = ApikeyCreate(title="MyApikey", auth_user=current_user)
        await apikey_manager.create(data)
        await uow.commit()
    yield data


@pytest.fixture(autouse=True)
def override_deps(apikey_secret):
    logger.debug("Override deps for apikey tests")

    async def apikey_auth_closure(apikey_value: str = Header(None, alias="X-API-Key")) -> AuthUser:
        if not apikey_value:
            raise HTTPException(status_code=401, detail="Invalid API Key")

        async with container.unit_of_work_factory().create_uow() as uow:
            apikey_manager = ApikeyManager(uow)
            apikey = await apikey_manager.get_by_secret(apikey_value)
        return apikey.auth_user

    app.dependency_overrides[auth_closure] = apikey_auth_closure
    yield
    app.dependency_overrides[auth_closure] = auth_closure


class TestCreatePlanWithApikey:
    @pytest.mark.asyncuio
    async def test_endpoint_with_good_secret(self, apikey_client, apikey_secret, plan_payload):
        response = await apikey_client.post("/plan", json=plan_payload)
        response.raise_for_status()

    @pytest.mark.asyncuio
    async def test_endpoint_with_bad_secret(self, apikey_client, apikey_secret, plan_payload):
        headers = {"X-API-Key": f"{apikey_secret.public_id}:any_bad_secret"}
        response = await apikey_client.post("/plan", json=plan_payload, headers=headers)
        assert response.status_code == 400

    @pytest.mark.asyncuio
    async def test_endpoint_without_headers(self, plan_payload):
        async with get_async_client() as c:
            response = await c.post("/plan", json=plan_payload)
        assert response.status_code == 401

    @pytest.mark.asyncuio
    async def test_endpoint_with_incorrect_headers(self, apikey_client, apikey_secret, plan_payload):
        headers = {"X-API-Key": "random_string"}
        response = await apikey_client.post("/plan", json=plan_payload, headers=headers)
        assert response.status_code == 400
