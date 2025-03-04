from uuid import uuid4

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
from tests.conftest import current_user, client
from tests.fakes import simple_plan, plan_with_usage_rates, plan_with_discounts, event_handler
from tests.helpers import check_changes

container = get_container()


async def full_update_plan(plan: Plan, client_):
    payload = PlanUpdate.from_plan(plan).model_dump(mode="json")
    url = f"/plan/{plan.id}"
    await client_.put(url, json=payload)


class TestCreate:
    @staticmethod
    def plan_payload(with_rates=False, with_discounts=False):
        plan = Plan("Simple", 100, "USD", uuid4(), Period.Monthly)
        if with_rates:
            plan.usage_rates.add(UsageRate("First", "first", "GB", 100, Period.Monthly))
            plan.usage_rates.add(UsageRate("Second", "second", "call", 120, Period.Daily))
        if with_discounts:
            plan.discounts.add(Discount("First", "first", "desc", 0.2, get_current_datetime()))
            plan.discounts.add(Discount("Second", "sec", "desc", 0.4, get_current_datetime()))
        return PlanCreate.from_plan(plan).model_dump(mode="json")

    @pytest.mark.asycnio
    async def test_create_simple_plan(self, current_user, event_handler, client):
        data = self.plan_payload()
        response = await client.post("/plan", json=data)
        response.raise_for_status()

        assert len(event_handler.events) == 1
        _plan_created = event_handler.pop(PlanCreated)

    @pytest.mark.asyncio
    async def test_create_plan_with_usage_rates(self, current_user, event_handler, client):
        data = self.plan_payload(with_rates=True)
        response = await client.post("/plan", json=data)
        response.raise_for_status()

        assert len(event_handler.events) == 1
        _plan_created = event_handler.pop(PlanCreated)

    @pytest.mark.asyncio
    async def test_create_plan_with_discounts(self, current_user, event_handler, client):
        data = self.plan_payload(with_discounts=True)
        response = await client.post("/plan", json=data)
        response.raise_for_status()

        assert len(event_handler.events) == 1
        _plan_created = event_handler.pop(PlanCreated)


class TestGet:
    @pytest.mark.asyncio
    async def test_get_one_by_id(self, simple_plan, client):
        response = await client.get(f"/plan/{simple_plan.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_with_usage_rates(self, plan_with_usage_rates, client):
        response = await client.get(f"/plan/{plan_with_usage_rates.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_selected(self, simple_plan, plan_with_usage_rates, client):
        params = {"ids": [plan_with_usage_rates.id]}
        response = await client.get(f"/plan/", params=params)
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestUpdate:
    @pytest.mark.asyncio
    async def test_change_plan_title(self, simple_plan, event_handler, client):
        simple_plan.title = "UPDATED"
        await full_update_plan(simple_plan, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "title": "UPDATED",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_add_usage_rates_to_plan(self, simple_plan, event_handler, client):
        simple_plan.usage_rates.add(
            UsageRate("Hello", "first", "GB", 100_000, Period.Daily)
        )
        await full_update_plan(simple_plan, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "usage_rates.first": "action:added",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_plan_usage_rate(self, plan_with_usage_rates, event_handler, client):
        target_rate = plan_with_usage_rates.usage_rates.get("first")
        target_rate.title = "UPDATED"

        await full_update_plan(plan_with_usage_rates, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "usage_rates.first": "action:updated",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_remove_plan_usage_rate(self, plan_with_usage_rates, event_handler, client):
        plan_with_usage_rates.usage_rates.remove("first")
        await full_update_plan(plan_with_usage_rates, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "usage_rates.first": "action:removed",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_add_discount_plan(self, simple_plan, event_handler, client):
        simple_plan.discounts.add(
            Discount("Hello", "first", "GB", 0.2, get_current_datetime())
        )
        await full_update_plan(simple_plan, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "discounts.first": "action:added",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_plan_discount(self, plan_with_discounts, event_handler, client):
        target_discount = plan_with_discounts.discounts.get("first")
        target_discount.title = "UPDATED"

        await full_update_plan(plan_with_discounts, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "discounts.first": "action:updated",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_remove_plan_discount(self, plan_with_discounts, event_handler, client):
        plan_with_discounts.discounts.remove("first")
        await full_update_plan(plan_with_discounts, client)

        assert len(event_handler.events) == 1
        plan_updated = event_handler.pop(PlanUpdated)
        expected = {
            "discounts.first": "action:removed",
            "updated_at": get_current_datetime(),
        }
        check_changes(plan_updated.changes, expected)


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_by_id(self, simple_plan, event_handler, client):
        response = await client.delete(f"/plan/{simple_plan.id}")
        response.raise_for_status()

        assert len(event_handler.events) == 1
        _plan_deleted = event_handler.pop(PlanDeleted)

    @pytest.mark.asyncio
    async def test_delete_selected(self, simple_plan, plan_with_usage_rates, event_handler, client):
        params = {"ids": [simple_plan.id]}
        response = await client.delete(f"/plan/{simple_plan.id}", params=params)
        response.raise_for_status()

        assert len(event_handler.events) == 1
        _plan_deleted = event_handler.pop(PlanDeleted)

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.plan_repo().get_selected(PlanSby())
            assert len(real) == 1
