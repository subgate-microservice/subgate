from typing import Type

import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.shared.event_driven.bus import Context
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.schemas import SubscriptionCreate, SubscriptionUpdate
from backend.subscription.application import subscription_service
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import (Subscription, SubscriptionPaused, SubscriptionUpdated,
                                                      SubscriptionUsageAdded, SubscriptionResumed,
                                                      SubscriptionUsageUpdated)
from backend.subscription.domain.usage import Usage
from tests.conftest import current_user, get_async_client

container = get_container()


@pytest.fixture()
def event_handler():
    class EventHandler:
        def __init__(self):
            self.events = {}

        async def handle_subscription_paused(self, event: SubscriptionPaused, _context: Context):
            logger.debug(event)
            self.events[SubscriptionPaused] = event

        async def handle_subscription_updated(self, event: SubscriptionUpdated, _context: Context):
            logger.debug(event)
            self.events[SubscriptionUpdated] = event

        async def handle_subscription_usage_added(self, event: SubscriptionUsageAdded, _context):
            logger.debug(event)
            self.events[SubscriptionUsageAdded] = event

        async def handle_subscription_resumed(self, event: SubscriptionResumed, _context):
            logger.debug(event)
            self.events[SubscriptionResumed] = event

        async def handle_subscription_usage_updated(self, event: SubscriptionUsageUpdated, _context):
            logger.debug(event)
            self.events[SubscriptionUsageUpdated] = event

        def get(self, event_class: Type[Event]):
            return self.events.get(event_class)

    handler = EventHandler()
    container.eventbus().subscribe(SubscriptionPaused, handler.handle_subscription_paused)
    container.eventbus().subscribe(SubscriptionUpdated, handler.handle_subscription_updated)
    container.eventbus().subscribe(SubscriptionUsageAdded, handler.handle_subscription_usage_added)
    container.eventbus().subscribe(SubscriptionResumed, handler.handle_subscription_resumed)
    container.eventbus().subscribe(SubscriptionUsageUpdated, handler.handle_subscription_usage_updated)

    yield handler

    handler.subscription_paused = None
    container.eventbus().unsubscribe(SubscriptionPaused, handler.handle_subscription_paused)


@pytest_asyncio.fixture()
async def simple_sub(current_user) -> Subscription:
    user, token, expected_status_code = current_user

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")

    async with container.unit_of_work_factory().create_uow() as uow:
        await subscription_service.create_subscription(sub, uow)
        await uow.commit()

    yield sub


@pytest_asyncio.fixture()
async def paused_sub(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")

    sub.pause()
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()

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
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()
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


class TestFullUpdate:
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
