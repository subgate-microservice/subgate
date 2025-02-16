from datetime import timedelta
from typing import Type, Optional

import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import container
from backend.events import EVENTS
from backend.shared.event_driven.base_event import Event
from backend.shared.utils import get_current_datetime
from backend.subscription.application import subscription_service
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription
from backend.subscription.domain.usage import Usage


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

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly, level=10)
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
