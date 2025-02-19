import pytest
import pytest_asyncio

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.subscription.application.subscription_service import create_subscription, save_updated_subscription
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.exceptions import ActiveStatusConflict
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import SubscriptionStatus, Subscription
from backend.subscription.domain.subscription_repo import SubscriptionSby
from tests.fakes import simple_sub

container = get_container()


@pytest.mark.asyncio
async def test_create_subscription_with_superior_plan(simple_sub):
    business_plan = Plan("Business", 100, "USD", simple_sub.auth_id, level=20)
    second_sub = Subscription.from_plan(business_plan, simple_sub.subscriber_id)

    async with container.unit_of_work_factory().create_uow() as uow:
        await create_subscription(second_sub, uow)
        await uow.commit()

    async with container.unit_of_work_factory().create_uow() as uow:
        all_subs = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(all_subs) == 2

        for sub in all_subs:
            if sub.plan_info.level == 10:
                assert sub.status == SubscriptionStatus.Paused
            else:
                assert sub.status == SubscriptionStatus.Active


@pytest.mark.asyncio
async def test_create_subscription_with_inferior_plan(simple_sub):
    free_plan = Plan("Free", 100, "USA", level=2, auth_id=simple_sub.auth_id)
    new_sub = Subscription.from_plan(free_plan, simple_sub.subscriber_id)

    async with container.unit_of_work_factory().create_uow() as uow:
        await create_subscription(new_sub, uow)
        await uow.commit()

    async with container.unit_of_work_factory().create_uow() as uow:
        all_subs = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(all_subs) == 2

        for sub in all_subs:
            if sub.plan_info.level == 2:
                assert sub.status == SubscriptionStatus.Paused
            else:
                assert sub.status == SubscriptionStatus.Active


@pytest.mark.asyncio
async def test_create_subscription_with_the_same_plan(simple_sub):
    plan = Plan("Simple", 100, "USD", simple_sub.auth_id, Period.Monthly, level=10)
    second_sub = Subscription.from_plan(plan, simple_sub.subscriber_id)

    async with container.unit_of_work_factory().create_uow() as uow:
        await create_subscription(second_sub, uow)
        await uow.commit()

    async with container.unit_of_work_factory().create_uow() as uow:
        all_subs = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(all_subs) == 2
        assert all_subs[0].status == SubscriptionStatus.Active
        assert all_subs[1].status == SubscriptionStatus.Paused


class TestCreateManySubscriptionForSubscriberId:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.auth_user = AuthUser()
        self.subscriber_id = "AnySubID"
        self.inferior_plan = Plan("Free", 100, "USD", self.auth_user.id, level=1)
        self.plan = Plan("Personal", 100, "USD", self.auth_user.id, level=10)
        self.superior_plan = Plan("Business", 100, "USD", self.auth_user.id, level=20)

    async def create_first_subscription(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription.from_plan(self.plan, self.subscriber_id)
            await create_subscription(subscription, uow)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_one_by_id(subscription.id)
            assert real.status == SubscriptionStatus.Active

    async def create_second_subscription_with_the_same_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription.from_plan(self.plan, self.subscriber_id)
            await create_subscription(subscription, uow)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_one_by_id(subscription.id)
            assert real.status == SubscriptionStatus.Paused

    async def create_third_subscription_with_superior_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription.from_plan(self.superior_plan, self.subscriber_id)
            await create_subscription(subscription, uow)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            subs = await uow.subscription_repo().get_selected(SubscriptionSby())
            assert len(subs) == 3
            for sub in subs:
                if sub.id == subscription.id:
                    assert sub.status == SubscriptionStatus.Active
                else:
                    assert sub.status == SubscriptionStatus.Paused

    async def create_forth_subscription_with_inferior_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription.from_plan(self.inferior_plan, self.subscriber_id)
            await create_subscription(subscription, uow)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            subs = await uow.subscription_repo().get_selected(SubscriptionSby())
            assert len(subs) == 4
            for sub in subs:
                if sub.plan_info.level == 20:
                    assert sub.status == SubscriptionStatus.Active
                else:
                    assert sub.status == SubscriptionStatus.Paused

    async def create_fifth_subscription_with_inferior_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription.from_plan(self.inferior_plan, self.subscriber_id)
            await create_subscription(subscription, uow)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            subs = await uow.subscription_repo().get_selected(SubscriptionSby())
            assert len(subs) == 5
            for sub in subs:
                if sub.plan_info.level == 20:
                    assert sub.status == SubscriptionStatus.Active
                else:
                    assert sub.status == SubscriptionStatus.Paused

    @pytest.mark.asyncio
    async def test_foo(self):
        await self.create_first_subscription()
        await self.create_second_subscription_with_the_same_plan()
        await self.create_third_subscription_with_superior_plan()
        await self.create_forth_subscription_with_inferior_plan()
        await self.create_fifth_subscription_with_inferior_plan()


class TestResumePausedSubscriptionWhileActiveOneExists:
    @pytest_asyncio.fixture(autouse=True)
    async def setup_method(self):
        auth_user = AuthUser()
        subscriber_id = "AnySubID"
        plan = Plan("Personal", 100, "USD", auth_user.id, level=10)
        self.active = Subscription.from_plan(plan, subscriber_id)

        self.paused = Subscription.from_plan(plan, subscriber_id)
        self.paused.pause()

        async with container.unit_of_work_factory().create_uow() as uow:
            await uow.subscription_repo().add_many([self.active, self.paused])
            await uow.commit()

    @pytest.mark.asyncio
    async def test_foo(self):
        with pytest.raises(ActiveStatusConflict):
            async with container.unit_of_work_factory().create_uow() as uow:
                self.paused.resume()
                await save_updated_subscription(self.paused, uow)
                await uow.commit()
