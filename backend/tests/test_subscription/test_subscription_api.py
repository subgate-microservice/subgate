import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.subscription.adapters.schemas import SubscriptionCreate
from backend.subscription.application import subscription_service
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription, SubscriptionPaused, SubscriptionUpdated
from tests.conftest import current_user, get_async_client


async def event_handler(event: Event, _context) -> None:
    logger.debug(event)


container = get_container()
container.eventbus().subscribe(SubscriptionPaused, event_handler)
container.eventbus().subscribe(SubscriptionUpdated, event_handler)


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


class TestUpdate:
    @pytest.mark.asyncio
    async def test_pause_subscription(self, current_user, simple_sub):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            simple_sub.pause()
            payload = SubscriptionCreate.from_subscription(simple_sub).model_dump(mode="json")

            response = await client.put(f"/subscription/{simple_sub.id}", json=payload, headers=headers)
            print(response.json())
            assert response.status_code == expected_status_code
