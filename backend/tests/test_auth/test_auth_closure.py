from uuid import uuid4

import pytest
import pytest_asyncio
from loguru import logger

from backend.auth.application.apikey_service import ApikeyCreate, ApikeyManager
from backend.auth.infra.apikey.auth_closure_factory import ApikeyAuthClosureFactory
from backend.auth.infra.fastapi_users.auth_closure_factory import FastapiUsersAuthClosureFactory
from backend.auth.infra.other.complex_factory import ComplexFactory
from backend.bootstrap import get_container, auth_closure
from backend.main import app
from backend.subscription.adapters.schemas import PlanCreate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from tests.conftest import get_async_client, client as token_client, current_user

container = get_container()


@pytest_asyncio.fixture()
async def apikey_client(current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        apikey_create = ApikeyCreate(title="AnyTitle", auth_user=current_user)
        manager = ApikeyManager(uow)
        await manager.create(apikey_create)
        await uow.commit()

    async with get_async_client() as c:
        c.headers = {"X-API-Key": f"{apikey_create.public_id}:{apikey_create.secret}"}
        yield c


def plan_payload():
    plan = Plan("Simple", 100, "USD", uuid4(), Period.Monthly)
    return PlanCreate.from_plan(plan).model_dump(mode="json")


class TestComplexClosure:
    @pytest.fixture(autouse=True, scope="class")
    def override_auth_closure_into_complex_factory(self):
        logger.debug("Overriding auth closure factory...")
        apikey_factory = ApikeyAuthClosureFactory(container.unit_of_work_factory())
        token_factory = FastapiUsersAuthClosureFactory(container.fastapi_users())
        factory = ComplexFactory(token_factory, apikey_factory)

        app.dependency_overrides[auth_closure] = factory.fastapi_closure()

        yield

        app.dependency_overrides[auth_closure] = auth_closure

    @pytest.mark.asyncio
    async def test_with_session_token(self, token_client):
        data = plan_payload()
        response = await token_client.post("/plan", json=data)
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_with_apikey(self, apikey_client):
        data = plan_payload()
        response = await apikey_client.post("/plan", json=data)
        response.raise_for_status()
