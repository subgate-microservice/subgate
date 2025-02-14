import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.plan_api import PlanCreate
from backend.subscription.adapters.schemas import PlanUpdate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan, PlanCreated, PlanUpdated
from backend.subscription.domain.usage import UsageRate
from tests.conftest import current_user, get_async_client

container = get_container()


async def event_handler(event, _context):
    logger.debug(event)


container.eventbus().subscribe(PlanCreated, event_handler)
container.eventbus().subscribe(PlanUpdated, event_handler)


@pytest_asyncio.fixture()
async def simple_plan(current_user):
    user, token, expected_status_code = current_user
    plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(plan)
        await uow.commit()
    yield plan


@pytest_asyncio.fixture()
async def with_usage_rates(current_user):
    user, token, expected_status_code = current_user
    plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
    plan.usage_rates.add(UsageRate("First", "first", "GB", 100, Period.Monthly))
    plan.usage_rates.add(UsageRate("Second", "second", "call", 120, Period.Daily))
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(plan)
        await uow.commit()
    yield plan


class TestCreate:
    @pytest.mark.asycnio
    async def test_create_simple_plan(self, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
            payload = PlanCreate.from_plan(plan).model_dump(mode="json")
            response = await client.post(f"/plan/", json=payload, headers=headers)
            assert response.status_code == expected_status_code

    @pytest.mark.asyncio
    async def test_create_plan_with_usage_rates(self, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
            plan.usage_rates.add(UsageRate("First", "first", "GB", 100, Period.Monthly))
            plan.usage_rates.add(UsageRate("Second", "second", "call", 120, Period.Daily))

            payload = PlanCreate.from_plan(plan).model_dump(mode="json")
            response = await client.post(f"/plan/", json=payload, headers=headers)
            assert response.status_code == expected_status_code

    @pytest.mark.asyncio
    async def test_create_plan_with_discounts(self, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
            plan.discounts.add(Discount("First", "first", "desc", 0.2, get_current_datetime()))
            plan.discounts.add(Discount("Second", "sec", "desc", 0.4, get_current_datetime()))

            payload = PlanCreate.from_plan(plan).model_dump(mode="json")
            response = await client.post(f"/plan/", json=payload, headers=headers)
            assert response.status_code == expected_status_code


class TestGet:
    @pytest.mark.asyncio
    async def test_get_one_by_id(self, simple_plan, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            response = await client.get(f"/plan/{simple_plan.id}", headers=headers)
            assert response.status_code == expected_status_code

    @pytest.mark.asyncio
    async def test_get_with_usage_rates(self, with_usage_rates, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            response = await client.get(f"/plan/{with_usage_rates.id}", headers=headers)
            assert response.status_code == expected_status_code


class TestUpdate:
    @pytest.mark.asyncio
    async def test_add_usages_to_plan(self, simple_plan, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_plan.usage_rates.add(
                UsageRate("first", "Hello", "GB", 100_000, Period.Daily)
            )
            payload = PlanUpdate.from_plan(simple_plan).model_dump(mode="json")
            response = await client.put(f"/plan/{simple_plan.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code
