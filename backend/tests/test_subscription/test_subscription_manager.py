import random
from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.application.subscription_manager import SubManager
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription
from backend.subscription.domain.enums import SubscriptionStatus
from backend.subscription.domain.subscription_repo import SubscriptionSby
from backend.subscription.domain.usage import Usage

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
    plan = Plan("Business", 100, "USD", auth_user.id, billing_cycle=Period.Monthly)
    yield plan


@pytest_asyncio.fixture()
async def expired_subs_with_active_status(plan, subscriber_ids):
    subs = []
    for subscriber_id in subscriber_ids:
        sub = Subscription.from_plan(plan, subscriber_id)
        sub.billing_info.last_billing = get_current_datetime() - timedelta(32)
        subs.append(sub)
    async with get_container().unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_many(subs)
        await uow.commit()
    yield subs


@pytest_asyncio.fixture()
async def paused_subs(plan, subscriber_ids):
    subs = []
    for subscriber_id in subscriber_ids:
        sub = Subscription.from_plan(plan, subscriber_id)
        sub.billing_info.last_billing = get_current_datetime() - timedelta(100)
        sub._created_at = get_current_datetime() - timedelta(101)
        sub._paused_from = get_current_datetime() - timedelta(90)
        sub._status = SubscriptionStatus.Paused
        subs.append(sub)
    async with get_container().unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_many(subs)
        await uow.commit()
    yield subs


@pytest.mark.asyncio
async def test_manage_subscriptions_change_statuses(expired_subs_with_active_status):
    manager = SubManager(container.unit_of_work_factory())
    await manager.manage_expired_subscriptions()

    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Expired}))
        assert len(real) == len(expired_subs_with_active_status)


@pytest.mark.asyncio
async def test_manage_subscriptions_resume_paused_subs(expired_subs_with_active_status, paused_subs):
    manager = SubManager(container.unit_of_work_factory())
    await manager.manage_expired_subscriptions()

    async with container.unit_of_work_factory().create_uow() as uow:
        # Проверяем, что истекшие подписки сменили статус
        expired_real = await uow.subscription_repo().get_selected(
            SubscriptionSby(statuses={SubscriptionStatus.Expired}))
        assert len(expired_real) == len(expired_subs_with_active_status)

        # Проверяем, что на каждую истекшую подписку мы возобновили (=забрали) подписку со статусом Paused
        paused_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Paused}))
        assert len(paused_real) == len(paused_subs) - len(expired_real)

        # Проверяем, что мы по-прежнему имеем идентичное количество активных подписок, так как мы их заменили
        active_real = await uow.subscription_repo().get_selected(SubscriptionSby(statuses={SubscriptionStatus.Active}))
        assert len(active_real) == len(expired_subs_with_active_status)


@pytest.mark.asyncio
async def test_autorenew_subscription(plan):
    # Before
    sub = Subscription.from_plan(plan, "AnySubscriberId", )
    sub.autorenew = True
    sub.billing_info.last_billing = get_current_datetime() - timedelta(32)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()

    # Test
    manager = SubManager(container.unit_of_work_factory())
    await manager.manage_expired_subscriptions()
    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.subscription_repo().get_one_by_id(sub.id)
        assert real.status == SubscriptionStatus.Active
        assert real.billing_info.last_billing.date() == get_current_datetime().date()


@pytest.mark.asyncio
async def test_subscription_manager_renew_usages(plan):
    sub = Subscription.from_plan(plan, "AnySubscriberId")
    sub.usages.add(
        Usage(
            title="AnyTitle",
            code="need_to_renew",
            unit="GB",
            available_units=100,
            renew_cycle=Period.Monthly,
            used_units=13,
            last_renew=get_current_datetime() - timedelta(days=31, seconds=22),
        )
    )
    sub.usages.add(
        Usage(
            title="AnyTitle",
            code="just_expired",
            unit="GB",
            available_units=300,
            renew_cycle=Period.Monthly,
            used_units=200,
            last_renew=get_current_datetime(),
        )
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()

    # Test
    manager = SubManager(container.unit_of_work_factory())
    await manager.manage_usages()

    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.subscription_repo().get_one_by_id(sub.id)
        assert real.usages.get("need_to_renew").used_units == 0
        assert real.usages.get("just_expired").used_units == 200


class TestSubscriptionManagerResumeSubscriptionWithHighestPlanLevel:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        self.auth_user = AuthUser()
        self.subscriber_id = "AnySubscriberID"
        self.subs = []
        for i in range(1, 11):
            plan = Plan("Business", 100, "USD", self.auth_user.id, level=i)
            sub = Subscription.from_plan(plan, self.subscriber_id)
            sub.pause()
            self.subs.append(sub)

        self.subs[3].resume()
        self.subs[3].billing_info.last_billing = get_current_datetime() - timedelta(299)

        async with container.unit_of_work_factory().create_uow() as uow:
            random.shuffle(self.subs)
            await uow.subscription_repo().add_many(self.subs)
            await uow.commit()

    @pytest.mark.asyncio
    async def test_foo(self):
        uow_factory = container.unit_of_work_factory()
        manager = SubManager(uow_factory)
        await manager.manage_expired_subscriptions()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_subscriber_active_one(
                self.subscriber_id,
                self.auth_user.id,
            )
            assert real.status == SubscriptionStatus.Active
            assert real.plan_info.level == 10
