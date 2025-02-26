from datetime import datetime, UTC, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.bootstrap import get_container
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.subscription import Subscription, PlanInfo, BillingInfo
from backend.subscription.domain.subscription_repo import SubscriptionSby

container = get_container()


class TestGetSelected:
    @pytest_asyncio.fixture()
    async def many_subs(self):
        subs = []
        for i in range(11):
            plan_info = PlanInfo(
                id=uuid4(),
                title="Personal",
                description=None,
                level=10,
                features=None,
            )
            billing_info = BillingInfo(
                price=100,
                currency="USD",
                billing_cycle=Period.Daily,
                last_billing=datetime(2021, 1, 1, tzinfo=UTC) + timedelta(days=i),
                saved_days=0,
            )
            sub = Subscription(
                plan_info=plan_info,
                billing_info=billing_info,
                subscriber_id=f"{i}",
                auth_id=uuid4(),
            )
            subs.append(sub)
        async with container.unit_of_work_factory().create_uow() as uow:
            await uow.subscription_repo().add_many(subs)
            await uow.commit()
        yield subs

    @pytest.mark.asyncio
    async def test_get_selected_lte(self, many_subs):
        lte = many_subs[3].expiration_date
        sby = SubscriptionSby(expiration_date_lte=lte)
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_selected(sby)
            assert len(real) == 4

    @pytest.mark.asyncio
    async def test_get_selected_lt(self, many_subs):
        lt = many_subs[3].expiration_date
        sby = SubscriptionSby(expiration_date_lt=lt)
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_selected(sby)
            assert len(real) == 3

    async def test_get_selected_gte(self, many_subs):
        gte = many_subs[5].expiration_date
        sby = SubscriptionSby(expiration_date_gte=gte)
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_selected(sby)
            assert len(real) == 6

    @pytest.mark.asyncio
    async def test_get_selected_gt(self, many_subs):
        gt = many_subs[5].expiration_date
        sby = SubscriptionSby(expiration_date_gt=gt)
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_selected(sby)
            assert len(real) == 5
