import asyncio
import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from loguru import logger

from backend.subscription.adapters.schemas import PlanCreate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan


class TestApikeyAuthenticationPerformance:
    @pytest_asyncio.fixture(scope="function")
    async def plan(self, apikey_client):
        plan = Plan("Simple", 100, "USD", uuid4(), Period.Monthly)
        data = PlanCreate.from_plan(plan).model_dump(mode="json")
        response = await apikey_client.post("/plan", json=data)
        response.raise_for_status()

        yield plan

    @pytest.mark.asyncio
    async def test_get_plan_without_concurrency(self, apikey_client, plan):
        start = datetime.datetime.now()
        for i in range(1_000):
            response = await apikey_client.get(f"/plan/{plan.id}")
            response.raise_for_status()
        end = datetime.datetime.now()
        logger.info(f"Total time is {(end - start).seconds} seconds")

    @pytest.mark.asyncio
    async def test_get_plan_without_with_concurrency(self, apikey_client, plan):
        start = datetime.datetime.now()

        tasks = []
        for i in range(1_000):
            coro = apikey_client.get(f"/plan/{plan.id}")
            task = asyncio.create_task(coro)
            tasks.append(task)
        await asyncio.gather(*tasks)

        end = datetime.datetime.now()
        logger.info(f"Total time is {(end - start).seconds} seconds")
