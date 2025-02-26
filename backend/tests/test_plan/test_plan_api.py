import pytest

from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.plan_api import PlanCreate
from backend.subscription.adapters.schemas import PlanUpdate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.events import PlanCreated, PlanUpdated, PlanDeleted
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.plan_repo import PlanSby
from backend.subscription.domain.usage import UsageRate
from tests.conftest import current_user, get_async_client
from tests.fakes import event_handler
from tests.fakes import simple_plan, plan_with_usage_rates
from tests.helpers import check_changes

container = get_container()


async def request(method: str, url, headers, expected_status_code, json=None):
    async with get_async_client() as client:
        response = await client.request(method, url, json=json, headers=headers)
        assert response.status_code == expected_status_code


async def post_request(plan: Plan, headers, expected_status_code):
    payload = PlanCreate.from_plan(plan).model_dump(mode="json")
    url = "/plan"
    await request("POST", url, headers, expected_status_code, json=payload)


async def put_request(plan: Plan, headers, expected_status_code):
    payload = PlanUpdate.from_plan(plan).model_dump(mode="json")
    url = f"/plan/{plan.id}"
    await request("PUT", url, headers, expected_status_code, json=payload)


class TestCreate:
    @pytest.mark.asycnio
    async def test_create_simple_plan(self, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        plan = PlanCreate(title="Simple", price=100, currency="USD", billing_cycle=Period.Monthly).to_plan(user.id)
        await post_request(plan, headers, expected_status_code)

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            _plan_created = event_handler.pop(PlanCreated)

    @pytest.mark.asyncio
    async def test_create_plan_with_usage_rates(self, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        plan = PlanCreate(title="Simple", price=100, currency="USD", billing_cycle=Period.Monthly).to_plan(user.id)
        plan.usage_rates.add(UsageRate("First", "first", "GB", 100, Period.Monthly))
        plan.usage_rates.add(UsageRate("Second", "second", "call", 120, Period.Daily))
        await post_request(plan, headers, expected_status_code)

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            _plan_created = event_handler.pop(PlanCreated)

    @pytest.mark.asyncio
    async def test_create_plan_with_discounts(self, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        plan = PlanCreate(title="Simple", price=100, currency="USD", billing_cycle=Period.Monthly).to_plan(user.id)
        plan.discounts.add(Discount("First", "first", "desc", 0.2, get_current_datetime()))
        plan.discounts.add(Discount("Second", "sec", "desc", 0.4, get_current_datetime()))
        await post_request(plan, headers, expected_status_code)

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            _plan_created = event_handler.pop(PlanCreated)


class TestGet:
    @pytest.mark.asyncio
    async def test_get_one_by_id(self, simple_plan, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            response = await client.get(f"/plan/{simple_plan.id}", headers=headers)
            assert response.status_code == expected_status_code

    @pytest.mark.asyncio
    async def test_get_with_usage_rates(self, plan_with_usage_rates, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            response = await client.get(f"/plan/{plan_with_usage_rates.id}", headers=headers)
            assert response.status_code == expected_status_code

    @pytest.mark.asyncio
    async def test_get_selected(self, simple_plan, plan_with_usage_rates, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            params = {"ids": [plan_with_usage_rates.id]}
            response = await client.get(f"/plan/", headers=headers, params=params)
            assert response.status_code == expected_status_code
            assert len(response.json()) == 1


class TestUpdate:
    @pytest.mark.asyncio
    async def test_add_usage_rates_to_plan(self, simple_plan, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        simple_plan.usage_rates.add(
            UsageRate("Hello", "first", "GB", 100_000, Period.Daily)
        )
        await put_request(simple_plan, headers, expected_status_code)

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            plan_updated = event_handler.pop(PlanUpdated)
            expected = {
                "usage_rates.first": "action:added",
                "updated_at": get_current_datetime(),
            }
            check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_plan_usage_rate(self, plan_with_usage_rates, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        target_rate = plan_with_usage_rates.usage_rates.get("first")
        target_rate.title = "UPDATED"

        await put_request(plan_with_usage_rates, headers, expected_status_code)

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            plan_updated = event_handler.pop(PlanUpdated)
            expected = {
                "usage_rates.first": "action:updated",
                "updated_at": get_current_datetime(),
            }
            check_changes(plan_updated.changes, expected)


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_by_id(self, simple_plan, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            response = await client.delete(f"/plan/{simple_plan.id}", headers=headers)
            assert response.status_code == expected_status_code

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            _plan_deleted = event_handler.pop(PlanDeleted)

    @pytest.mark.asyncio
    async def test_delete_selected(self, simple_plan, plan_with_usage_rates, current_user, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            params = {"ids": [simple_plan.id]}
            response = await client.delete(f"/plan/{simple_plan.id}", headers=headers, params=params)
            assert response.status_code == expected_status_code

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.plan_repo().get_selected(PlanSby())
            assert len(real) == 1

        if expected_status_code < 400:
            assert len(event_handler.events) == 1
            _plan_deleted = event_handler.pop(PlanDeleted)
