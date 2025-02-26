from datetime import timedelta
from typing import Type, Optional, Union

import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import container
from backend.events import EVENTS
from backend.shared.event_driven.base_event import Event
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription
from backend.subscription.domain.usage import Usage, UsageRate
from backend.webhook.adapters.schemas import WebhookCreate
from backend.webhook.domain.webhook import Webhook


async def save_sub(sub: Subscription) -> None:
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()


async def save_plan(plan: Plan) -> None:
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(plan)
        await uow.commit()


def set_dates(item: Union[Subscription, Plan, Webhook]):
    dt = get_current_datetime() - timedelta(seconds=2)
    item.updated_at = dt
    item.__dict__["_d_created_at"] = dt


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
async def simple_plan(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly, level=10)
    set_dates(plan)
    await save_plan(plan)
    yield plan


@pytest_asyncio.fixture()
async def plan_with_usage_rates(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    plan.usage_rates.add(UsageRate("First", "first", "GB", 100, Period.Monthly))
    plan.usage_rates.add(UsageRate("Second", "second", "call", 120, Period.Daily))
    set_dates(plan)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(plan)
        await uow.commit()
    yield plan


@pytest_asyncio.fixture()
async def simple_sub(current_user) -> Subscription:
    user, token, expected_status_code = current_user

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly, level=10)
    sub = Subscription.from_plan(plan, "AmyID")
    set_dates(sub)
    await save_sub(sub)

    yield sub


@pytest_asyncio.fixture()
async def paused_sub(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.pause()
    set_dates(sub)
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def expired_sub(current_user):
    user, token, expected_status_code = current_user
    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.billing_info.last_billing = get_current_datetime() - timedelta(100)
    sub.expire()
    set_dates(sub)
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
    set_dates(sub)
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
    set_dates(sub)
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def sub_with_fields(current_user):
    user, token, expected_status_code = current_user

    plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
    sub = Subscription.from_plan(plan, "AmyID")
    sub.fields = {"any_value": 1, "inner_items": [1, 2, 3, 4, 5]}
    set_dates(sub)
    await save_sub(sub)
    yield sub


@pytest_asyncio.fixture()
async def simple_webhook(current_user):
    user, token, expected_status_code = current_user

    async with container.unit_of_work_factory().create_uow() as uow:
        hook = WebhookCreate(event_code="plan_created", target_url="http://my-site.com").to_webhook(user.id)
        set_dates(hook)
        await uow.webhook_repo().add_one(hook)
        await uow.commit()
    yield hook


@pytest_asyncio.fixture()
async def many_webhooks(current_user):
    user, token, expected_status_code = current_user

    hooks = []
    async with container.unit_of_work_factory().create_uow() as uow:
        for i in range(11):
            hook = WebhookCreate(event_code="plan_created", target_url=f"http://my-site-{i}.com").to_webhook(user.id)
            await uow.webhook_repo().add_one(hook)
            set_dates(hook)
            hooks.append(hook)
        await uow.commit()
    yield hooks
