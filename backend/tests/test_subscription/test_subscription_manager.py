from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.application.subscription_manager import SubscriptionManager, SubscriptionUsageManager
from backend.subscription.domain.cycle import Cycle, CycleCode
from backend.subscription.domain.plan import Plan, Usage
from backend.subscription.domain.subscription import Subscription, SubscriptionStatus
from backend.subscription.domain.subscription_repo import SubscriptionSby

container = get_container()


@pytest_asyncio.fixture()
async def auth_user():
    yield AuthUser(id=uuid4())


@pytest_asyncio.fixture()
async def subscriber_ids():
    data = ["First", "Second", "Third"]
    yield data


@pytest_asyncio.fixture()
async def plan(auth_user):
    plan = Plan(
        title="Business",
        price=100,
        currency="USD",
        billing_cycle=Cycle(title="Monthly", code="Monthly", cycle_in_days=31),
        level=10,
        auth_id=auth_user.id if auth_user else uuid4(),
    )
    yield plan


@pytest_asyncio.fixture()
async def expired_subs_with_active_status(plan, subscriber_ids):
    subs = []
    for subscriber_id in subscriber_ids:
        sub = Subscription(
            id=uuid4(),
            auth_id=plan.auth_id,
            subscriber_id=subscriber_id,
            plan=plan,
            status=SubscriptionStatus.Active,
            usages=[],
            last_billing=get_current_datetime() - timedelta(32),
            created_at=get_current_datetime() - timedelta(33),
            updated_at=get_current_datetime(),
            paused_from=None,
            autorenew=False,
        )
        subs.append(sub)
    async with get_container().unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_many(subs)
        await uow.commit()
    yield subs


@pytest_asyncio.fixture()
async def paused_subs(plan, subscriber_ids):
    subs = []
    for subscriber_id in subscriber_ids:
        sub = Subscription(
            id=uuid4(),
            auth_id=plan.auth_id,
            subscriber_id=subscriber_id,
            plan=plan,
            status=SubscriptionStatus.Paused,
            usages=[],
            last_billing=get_current_datetime() - timedelta(100),
            created_at=get_current_datetime() - timedelta(101),
            updated_at=get_current_datetime(),
            paused_from=get_current_datetime() - timedelta(90),
            autorenew=False,
        )
        subs.append(sub)
    async with get_container().unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_many(subs)
        await uow.commit()
    yield subs


@pytest.mark.asyncio
async def test_manage_subscriptions_change_statuses(expired_subs_with_active_status):
    bus = container.eventbus()
    uow_factory = container.unit_of_work_factory()
    manager = SubscriptionManager(uow_factory, bus)
    await manager.manage_expired_subscriptions()

    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Expired}))
        assert len(real) == len(expired_subs_with_active_status)


@pytest.mark.asyncio
async def test_manage_subscriptions_resume_paused_subs(expired_subs_with_active_status, paused_subs):
    bus = container.eventbus()
    uow_factory = container.unit_of_work_factory()
    manager = SubscriptionManager(uow_factory, bus)
    await manager.manage_expired_subscriptions()

    async with container.unit_of_work_factory().create_uow() as uow:
        # Проверяем, что истекшие подписки сменили статус
        expired_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Expired}))
        assert len(expired_real) == len(expired_subs_with_active_status)

        # Проверяем, что на каждую истекшую подписку мы возобновили (=забрали) подписку со статусом Paused
        paused_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Paused}))
        assert len(paused_real) == len(paused_subs) - len(expired_real)

        # Проверяем, что мы по-прежнему имеем идентичное количество активных подписок, так как мы их заменили
        active_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Active}))
        assert len(active_real) == len(expired_subs_with_active_status)


#
# @pytest.mark.asyncio
# async def test_rollback_when_events_were_failed(expired_subs_with_active_status, paused_subs):
#     class MockManager(SubscriptionManager):
#         async def _send_events(self):
#             raise Exception("Any exception in send_events() occurred")
#
#     bus = container.eventbus()
#     uow_factory = container.unit_of_work
#     manager = MockManager(uow_factory, bus)
#     await manager.manage_expired_subscriptions()
#
#     uow = container.unit_of_work_factory().create_uow()
#     expired_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Expired}))
#     assert len(expired_real) == 0
#
#     paused_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Paused}))
#     assert len(paused_real) == len(paused_subs)
#     for real, expected in zip(paused_real, paused_subs):
#         assert real.id == expected.id
#
#     active_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Active}))
#     assert len(active_real) == len(expired_subs_with_active_status)
#     for real, expected in zip(active_real, expired_subs_with_active_status):
#         assert real.id == expected.id


@pytest.mark.asyncio
async def test_autorenew_subscription(plan):
    # Before
    sub = Subscription(
        plan=plan,
        subscriber_id="AnySubscriberId",
        auth_id=uuid4(),
        last_billing=get_current_datetime() - timedelta(32),
        created_at=get_current_datetime() - timedelta(32, 1),
        autorenew=True,
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()

    # Test
    manager = SubscriptionManager(container.unit_of_work_factory(), container.eventbus())
    await manager.manage_expired_subscriptions()
    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.subscription_repo().get_one_by_id(sub.id)
        assert real.status == SubscriptionStatus.Active
        assert real.last_billing.date() == get_current_datetime().date()


@pytest.mark.asyncio
async def test_subscription_manager_renew_usages(plan):
    # Before
    usages = [
        Usage(
            title="AnyTitle",
            code="need_to_renew",
            unit="GB",
            available_units=100,
            used_units=13,
            last_renew=get_current_datetime() - timedelta(days=31, seconds=22),
            renew_cycle=Cycle.from_code(CycleCode.Monthly),
        ),
        Usage(
            title="AnyTitle",
            code="just_expired",
            unit="GB",
            available_units=300,
            used_units=200,
            last_renew=get_current_datetime(),
            renew_cycle=Cycle.from_code(CycleCode.Monthly),
        ),
    ]
    sub = Subscription(
        plan=plan,
        subscriber_id="AnySubscriberId",
        auth_id=uuid4(),
        usages=usages,
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()

    # Test
    manager = SubscriptionUsageManager(container.unit_of_work_factory(), container.eventbus())
    await manager.manage_usages()

    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.subscription_repo().get_one_by_id(sub.id)
        assert real.usages[0].used_units == 0
        assert real.usages[1].used_units == usages[1].used_units
