from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import Header, HTTPException
from loguru import logger

from backend.auth.application.apikey_service import ApikeyManager, ApikeyCreate
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.apikey.apikey_repo_sql import SqlApikeyRepo, ApikeySqlMapper
from backend.bootstrap import get_container, auth_closure
from backend.main import app
from backend.subscription.adapters.schemas import PlanCreate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from tests.conftest import client

container = get_container()


@pytest_asyncio.fixture()
async def apikey_secret(current_user):
    session_factory = container.session_factory()
    async with session_factory() as session:
        apikey_repo = SqlApikeyRepo(session, ApikeySqlMapper())
        apikey_manager = ApikeyManager(apikey_repo)
        data = ApikeyCreate(title="MyApikey", auth_user=current_user)
        await apikey_manager.create(data)
        await session.commit()
    yield data


@pytest.fixture(autouse=True)
def override_deps(apikey_secret):
    logger.debug("Override deps for apikey tests")

    async def apikey_auth_closure(apikey_value: str = Header(None, alias="X-API-Key")) -> AuthUser:
        if not apikey_value:
            raise HTTPException(status_code=401, detail="Invalid API Key")

        session_factory = container.session_factory()
        async with session_factory() as session:
            apikey_repo = SqlApikeyRepo(session, ApikeySqlMapper())
            apikey_manager = ApikeyManager(apikey_repo)
            apikey = await apikey_manager.get_by_secret(apikey_value)
        return apikey.auth_user

    app.dependency_overrides[auth_closure] = apikey_auth_closure


class TestCreatePlanWithApikey:
    @staticmethod
    def plan_payload():
        plan = Plan("Simple", 100, "USD", uuid4(), Period.Monthly)
        return PlanCreate.from_plan(plan).model_dump(mode="json")

    @pytest.mark.asyncui
    async def test_endpoint_with_good_secret(self, client, apikey_secret):
        headers = {"X-API-Key": f"{apikey_secret.public_id}:{apikey_secret.secret}"}
        data = self.plan_payload()
        response = await client.post("/plan", json=data, headers=headers, cookies=None)
        response.raise_for_status()

    @pytest.mark.asyncui
    async def test_endpoint_with_bad_secret(self, client, apikey_secret):
        headers = {"X-API-Key": f"{apikey_secret.public_id}:any_bad_secret"}
        data = self.plan_payload()
        response = await client.post("/plan", json=data, headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncui
    async def test_endpoint_without_headers(self, client, apikey_secret):
        data = self.plan_payload()
        response = await client.post("/plan", json=data, headers=None)
        assert response.status_code == 401
