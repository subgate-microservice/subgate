from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Cycle, CycleCode
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription, SubscriptionStatus
from backend.subscription.domain.subscription_repo import SubscriptionSby
from tests.fake_data import create_subscription

container = get_container()


@pytest_asyncio.fixture()
async def auth_user():
    yield AuthUser(id=uuid4())


@pytest_asyncio.fixture()
async def plan(auth_user):
    plan = Plan(
        title="Business",
        price=100,
        currency="USD",
        billing_cycle=Cycle.from_code(CycleCode.Monthly),
        level=10,
        auth_id=auth_user.id if auth_user else uuid4(),
    )
    yield plan


@pytest_asyncio.fixture()
async def expired_subs_with_active_status(plan):
    subs = []
    for _ in range(11):
        sub = Subscription(
            id=uuid4(),
            auth_id=plan.auth_id,
            subscriber_id=str(uuid4()),
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
async def active_subs(plan):
    subs = []
    for _ in range(11):
        sub = Subscription(
            id=uuid4(),
            auth_id=plan.auth_id,
            subscriber_id=str(uuid4()),
            plan=plan,
            status=SubscriptionStatus.Active,
            usages=[],
            last_billing=get_current_datetime() - timedelta(days=11),
            created_at=get_current_datetime() - timedelta(days=12),
            updated_at=get_current_datetime(),
            paused_from=None,
            autorenew=False,
        )
        subs.append(sub)
    async with get_container().unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_many(subs)
        await uow.commit()
    yield subs


class TestGetSelected:
    @pytest.mark.asyncio
    async def test_get_expired_subs(self, active_subs, expired_subs_with_active_status):
        async with get_container().unit_of_work_factory().create_uow() as uow:
            sby = SubscriptionSby(expiration_date_lt=get_current_datetime())
            repo = uow.subscription_repo()
            real = await repo.get_selected(sby)
            assert len(real) > 0
            assert len(real) == len(expired_subs_with_active_status)

    @pytest.mark.asyncio
    async def test_get_selected_with_expiration_date_filter(self):
        # Before
        async with container.unit_of_work_factory().create_uow() as uow:
            last_billings = [get_current_datetime() - timedelta(days=i) for i in range(25, 40)]
            subs = [create_subscription(last_billing=billing) for billing in last_billings]
            await uow.subscription_repo().add_many(subs)
            await uow.commit()

        # Test
        async with container.unit_of_work_factory().create_uow() as uow:
            sby = SubscriptionSby(expiration_date_lt=get_current_datetime())
            real = await uow.subscription_repo().get_selected(sby)
            assert len(real) > 0

            expected = [sub for sub in subs if sub.expiration_date < get_current_datetime()]
            assert len(real) == len(expected)
            assert {x.id for x in real} == {x.id for x in expected}
