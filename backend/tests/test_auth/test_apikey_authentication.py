import asyncio
import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import Header, HTTPException
from loguru import logger

from backend.auth.application.apikey_service import ApikeyManager, ApikeyCreate
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container, auth_closure
from backend.main import app
from backend.subscription.adapters.schemas import PlanCreate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan

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
    @staticmethod
    def plan_payload():
        plan = Plan("Simple", 100, "USD", uuid4(), Period.Monthly)
        return PlanCreate.from_plan(plan).model_dump(mode="json")

    @pytest.mark.asyncui
    async def test_endpoint_with_good_secret(self, apikey_client, apikey_secret):
        data = self.plan_payload()
        response = await apikey_client.post("/plan", json=data)
        response.raise_for_status()

    @pytest.mark.asyncui
    async def test_endpoint_with_bad_secret(self, apikey_client, apikey_secret):
        headers = {"X-API-Key": f"{apikey_secret.public_id}:any_bad_secret"}
        data = self.plan_payload()
        response = await apikey_client.post("/plan", json=data, headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncui
    async def test_endpoint_without_headers(self, apikey_client, apikey_secret):
        data = self.plan_payload()
        response = await apikey_client.post("/plan", json=data, headers=None)
        assert response.status_code == 401

    @pytest.mark.asyncui
    async def test_endpoint_with_incorrect_headers(self, apikey_client, apikey_secret):
        headers = {"X-API-Key": "random_string"}
        data = self.plan_payload()
        response = await apikey_client.post("/plan", json=data, headers=headers)
        assert response.status_code == 400


class TestApikeyAuthenticationPerformance:
    @pytest_asyncio.fixture(scope="function")
    async def plan(self, apikey_client):
        plan = Plan("Simple", 100, "USD", uuid4(), Period.Monthly)
        data = PlanCreate.from_plan(plan).model_dump(mode="json")
        response = await apikey_client.post("/plan", json=data)
        response.raise_for_status()

        yield plan

    @pytest.mark.asyncio
    async def test_get_plan_without_cache_and_without_concurrency(self, apikey_client, plan):
        start = datetime.datetime.now()
        for i in range(100):
            response = await apikey_client.get(f"/plan/{plan.id}")
            response.raise_for_status()
        end = datetime.datetime.now()
        logger.info(f"Total time is {(end - start).seconds} seconds")

    @pytest.mark.asyncio
    async def test_get_plan_without_cache_but_with_concurrency(self, apikey_client, plan):
        start = datetime.datetime.now()

        tasks = []
        for i in range(100):
            coro = apikey_client.get(f"/plan/{plan.id}")
            task = asyncio.create_task(coro)
            tasks.append(task)
        await asyncio.gather(*tasks)

        end = datetime.datetime.now()
        logger.info(f"Total time is {(end - start).seconds} seconds")
