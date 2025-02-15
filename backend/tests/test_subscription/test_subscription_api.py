from typing import Optional

import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import get_container
from backend.shared.event_driven.bus import Context
from backend.subscription.adapters.schemas import SubscriptionCreate, SubscriptionUpdate
from backend.subscription.application import subscription_service
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription, SubscriptionPaused, SubscriptionUpdated
from tests.conftest import current_user, get_async_client

container = get_container()


@pytest.fixture()
def event_handler():
    class EventHandler:
        def __init__(self):
            self.subscription_paused: Optional[SubscriptionPaused] = None
            self.subscription_updated: Optional[SubscriptionUpdated] = None

        async def handle_subscription_paused(self, event: SubscriptionPaused, _context: Context):
            logger.debug(event)
            self.subscription_paused = event

        async def handle_subscription_updated(self, event: SubscriptionUpdated, _context: Context):
            logger.debug(event)
            self.subscription_updated = event

    handler = EventHandler()
    container.eventbus().subscribe(SubscriptionPaused, handler.handle_subscription_paused)
    container.eventbus().subscribe(SubscriptionUpdated, handler.handle_subscription_updated)

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
        assert event_handler.subscription_paused is not None
        assert event_handler.subscription_updated is not None
        assert set(event_handler.subscription_updated.changed_fields) == {"paused_from", "status"}
