import pytest
from loguru import logger

from backend.auth.infra.apikey.auth_closure_factory import ApikeyAuthClosureFactory
from backend.auth.infra.fastapi_users.auth_closure_factory import FastapiUsersAuthClosureFactory
from backend.auth.infra.other.complex_factory import ComplexFactory
from backend.bootstrap import get_container, auth_closure
from backend.main import app
from tests.conftest import client as token_client, apikey_client
from tests.fakes import plan_payload

container = get_container()


class TestComplexClosure:
    @pytest.fixture(autouse=True, scope="class")
    def override_auth_closure_into_complex_factory(self):
        logger.debug("Overriding auth closure factory...")
        apikey_factory = ApikeyAuthClosureFactory(container.unit_of_work_factory(), container.apikey_cache_manager())
        token_factory = FastapiUsersAuthClosureFactory(container.fastapi_users(), container.auth_token_cache_manager())
        factory = ComplexFactory(token_factory, apikey_factory)

        app.dependency_overrides[auth_closure] = factory.fastapi_closure()

        yield

        app.dependency_overrides[auth_closure] = auth_closure

    @pytest.mark.asyncio
    async def test_with_session_token(self, token_client, plan_payload):
        response = await token_client.post("/plan", json=plan_payload)
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_with_apikey(self, apikey_client, plan_payload):
        response = await apikey_client.post("/plan", json=plan_payload)
        response.raise_for_status()
