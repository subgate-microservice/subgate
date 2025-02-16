from datetime import timedelta
from typing import Type, Optional

import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import get_container
from backend.events import EVENTS
from backend.shared.event_driven.base_event import Event
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.schemas import SubscriptionCreate, SubscriptionUpdate
from backend.subscription.application import subscription_service
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import (
    Subscription, SubscriptionPaused, SubscriptionUpdated, SubscriptionUsageAdded, SubscriptionResumed,
    SubscriptionUsageUpdated, SubscriptionUsageRemoved, SubscriptionDiscountUpdated, SubscriptionDiscountAdded,
    SubscriptionDiscountRemoved, SubscriptionStatus, SubscriptionRenewed,
)
from backend.subscription.domain.usage import Usage
from tests.conftest import current_user, get_async_client

container = get_container()


async def save_sub(sub: Subscription) -> None:
    async with container.unit_of_work_factory().create_uow() as uow:
        await subscription_service.create_subscription(sub, uow)
        await uow.commit()


@pytest.fixture()
def event_handler():
    class EventHandler:
        def __init__(self):
            self.events = {}

        async def handle_event(self, event: Event, _context):
            logger.debug(event)
            self.events[type(event)] = event

        def get[T](self, event_class: Type[T]) -> Optional[T]:
            return self.events.get(event_class)

    handler = EventHandler()
    for ev in EVENTS:
        container.eventbus().subscribe(ev, handler.handle_event)

    yield handler

    for ev in EVENTS:
        container.eventbus().unsubscribe(ev, handler.handle_event)


@pytest_asyncio.fixture()
async def simple_sub(current_user) -> Subscription:
    user, token, expected_status_code = current_user

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    await save_sub(sub)

    yield sub


@pytest_asyncio.fixture()
async def paused_sub(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.pause()
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def expired_sub(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.billing_info.last_billing = get_current_datetime() - timedelta(100)
    sub.expire()
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def sub_with_usages(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.usages.add(
        Usage(title="First", code="first", unit="GB", renew_cycle=Period.Monthly, available_units=111, used_units=0,
              last_renew=get_current_datetime())
    )
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def sub_with_discounts(current_user):
    user, token, expected_status_code = current_user

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.discounts.add(
        Discount(title="First", code="first", size=0.2, description="Black friday", valid_until=get_current_datetime())
    )
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def sub_with_fields(current_user):
    user, token, expected_status_code = current_user

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.fields = {"any_value": 1, "inner_items": [1, 2, 3, 4, 5]}
    await save_sub(sub)
    yield sub


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_simple_subscription(self, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
            subscription = Subscription.from_plan(plan, "AnyID")
            payload = SubscriptionCreate.from_subscription(subscription).model_dump(mode="json")

            response = await client.post(f"/subscription/", json=payload, headers=headers)
            assert response.status_code == expected_status_code


class TestStatusManagement:
    @pytest.mark.asyncio
    async def test_pause_subscription(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.pause()
            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_paused, sub_updated = event_handler.get(SubscriptionPaused), event_handler.get(SubscriptionUpdated)
        assert sub_paused is not None
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"paused_from", "status"}

    @pytest.mark.asyncio
    async def test_resume_subscription(self, current_user, paused_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            paused_sub.resume()
            payload = SubscriptionUpdate.from_subscription(paused_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{paused_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_resumed, sub_updated = event_handler.get(SubscriptionResumed), event_handler.get(SubscriptionUpdated)
        assert sub_resumed is not None
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"paused_from", "status"}

    @pytest.mark.asyncio
    async def test_renew_active_subscription(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.renew()
            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        assert len(event_handler.events) == 0

    @pytest.mark.asyncio
    async def test_renew_paused_subscription(self, current_user, paused_sub, event_handler):
        # Important!
        # Renew paused subscription is the same that resume paused subscription

        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            paused_sub._status = SubscriptionStatus.Active
            paused_sub._paused_from = None
            paused_sub.billing_info.last_billing = get_current_datetime()
            payload = SubscriptionUpdate.from_subscription(paused_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{paused_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_resumed, sub_updated = event_handler.get(SubscriptionResumed), event_handler.get(SubscriptionUpdated)
        assert sub_resumed is not None
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"paused_from", "status"}

    @pytest.mark.asyncio
    async def test_renew_expired_subscription(self, current_user, expired_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            expired_sub.renew()
            payload = SubscriptionUpdate.from_subscription(expired_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{expired_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_renewed, sub_updated = event_handler.get(SubscriptionRenewed), event_handler.get(SubscriptionUpdated)
        assert sub_renewed is not None
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"status", "billing_info.last_billing"}


class TestUsageManagement:
    @pytest.mark.asyncio
    async def test_add_usage(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.usages.add(Usage("First", "first", "GB", 100, Period.Monthly, 0, get_current_datetime()))
            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_updated, usage_added = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageAdded)
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"usages.first:added"}
        assert usage_added is not None
        assert usage_added.code == "first"

    @pytest.mark.asyncio
    async def test_update_usage(self, current_user, sub_with_usages, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            sub_with_usages.usages.get("first").increase(150)
            payload = SubscriptionUpdate.from_subscription(sub_with_usages).model_dump(mode="json")

            response = await client.put(f"/subscription/{sub_with_usages.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_updated, u_updated = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageUpdated)
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"usages.first:updated"}
        assert u_updated is not None
        assert u_updated.code == "first"
        assert u_updated.used_units == 150

    @pytest.mark.asyncio
    async def test_remove_usage(self, current_user, sub_with_usages, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            sub_with_usages.usages.remove("first")

            payload = SubscriptionUpdate.from_subscription(sub_with_usages).model_dump(mode="json")

            response = await client.put(f"/subscription/{sub_with_usages.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_updated, u_removed = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageRemoved)
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"usages.first:removed"}
        assert u_removed is not None
        assert u_removed.code == "first"


class TestDiscountManagement:
    @pytest.mark.asyncio
    async def test_add_discount(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.discounts.add(
                Discount(title="Second", code="second", size=0.5, description="Hello world",
                         valid_until=get_current_datetime())
            )
            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_updated, d_added = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionDiscountAdded)
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"discounts.second:added"}
        assert d_added is not None
        assert d_added.code == "second"

    @pytest.mark.asyncio
    async def test_remove_discount(self, current_user, sub_with_discounts, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            sub_with_discounts.discounts.remove("first")
            payload = SubscriptionUpdate.from_subscription(sub_with_discounts).model_dump(mode="json")

            response = await client.put(f"/subscription/{sub_with_discounts.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_updated, d_removed = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionDiscountRemoved)
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"discounts.first:removed"}
        assert d_removed is not None
        assert d_removed.code == "first"

    @pytest.mark.asyncio
    async def test_update_discount(self, current_user, sub_with_discounts, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            sub_with_discounts.discounts.get("first").title = "Hello world!"
            payload = SubscriptionUpdate.from_subscription(sub_with_discounts).model_dump(mode="json")

            response = await client.put(f"/subscription/{sub_with_discounts.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        sub_updated, d_updated = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionDiscountUpdated)
        assert sub_updated is not None
        assert set(sub_updated.changed_fields) == {"discounts.first:updated"}
        assert d_updated is not None
        assert d_updated.title == "Hello world!"


class TestOtherFieldsManagement:
    @pytest.mark.asyncio
    async def test_update_plan_info(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.plan_info.title = "Updated title"
            simple_sub.plan_info.level = 755
            simple_sub.plan_info.features = "Updated features"
            simple_sub.plan_info.description = "Updated description"

            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")
            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"plan_info.title", "plan_info.level", "plan_info.features",
                                                       "plan_info.description", }

    @pytest.mark.asyncio
    async def test_update_billing_info(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.billing_info.price = 99
            simple_sub.billing_info.currency = "EUR"
            simple_sub.billing_info.billing_cycle = Period.Semiannual
            simple_sub.billing_info.last_billing = get_current_datetime().replace(year=1999)

            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")
            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"billing_info.price", "billing_info.currency",
                                                       "billing_info.billing_cycle", "billing_info.last_billing", }

    @pytest.mark.asyncio
    async def test_update_fields(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.fields = {"Hello": 1, "World": 2}
            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")
            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"fields", }

    @pytest.mark.asyncio
    async def test_update_fields_inner_values(self, current_user, sub_with_fields, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            sub_with_fields.fields["any_value"] = "Updated"
            payload = SubscriptionUpdate.from_subscription(sub_with_fields).model_dump(mode="json")
            response = await client.put(f"/subscription/{sub_with_fields.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"fields", }

    @pytest.mark.asyncio
    async def test_update_autorenew(self, current_user, sub_with_fields, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            sub_with_fields.autorenew = True
            payload = SubscriptionUpdate.from_subscription(sub_with_fields).model_dump(mode="json")
            response = await client.put(f"/subscription/{sub_with_fields.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"autorenew"}

    @pytest.mark.asyncio
    async def test_update_subscriber_id(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.subscriber_id = "UpdatedID"
            payload = SubscriptionUpdate.from_subscription(simple_sub).model_dump(mode="json")
            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"subscriber_id"}
