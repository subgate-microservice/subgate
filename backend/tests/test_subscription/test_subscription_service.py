import pytest

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.subscription.application.subscription_service import SubscriptionService
from backend.subscription.domain.cycle import Cycle, CycleCode
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import SubscriptionStatus, Subscription
from backend.subscription.domain.subscription_repo import SubscriptionSby
from tests.fake_data import create_plan, create_subscription

container = get_container()


@pytest.mark.asyncio
async def test_create_subscription_with_superior_plan():
    # Before
    auth_user = AuthUser()
    subscriber_id = "AnySubId"
    personal_plan = create_plan(title="Personal", level=10, auth_user=AuthUser())
    first_sub = create_subscription(plan=personal_plan, subscriber_id=subscriber_id, auth_user=auth_user)

    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(first_sub)
        await uow.commit()

    # Test
    business_plan = create_plan(title="Business", level=20, auth_user=auth_user)
    second_sub = create_subscription(plan=business_plan, subscriber_id=subscriber_id, auth_user=auth_user)

    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        service = SubscriptionService(bus, uow)
        await service.create_one(second_sub)
        await uow.commit()

    async with container.unit_of_work_factory().create_uow() as uow:
        all_subs = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(all_subs) == 2

        for sub in all_subs:
            if sub.plan.level == 10:
                assert sub.status == SubscriptionStatus.Paused
            else:
                assert sub.status == SubscriptionStatus.Active


@pytest.mark.asyncio
async def test_create_subscription_with_inferior_plan():
    # Before
    auth_user = AuthUser()
    subscriber_id = "AnySubId"
    personal_plan = create_plan(title="Business", level=20, auth_user=auth_user)
    first_sub = create_subscription(plan=personal_plan, subscriber_id=subscriber_id, auth_user=auth_user)

    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(first_sub)
        await uow.commit()

    # Test
    business_plan = create_plan(title="Personal", level=10, auth_user=auth_user)
    second_sub = create_subscription(plan=business_plan, subscriber_id=subscriber_id, auth_user=auth_user)

    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        service = SubscriptionService(bus, uow)
        await service.create_one(second_sub)
        await uow.commit()

    async with container.unit_of_work_factory().create_uow() as uow:
        all_subs = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(all_subs) == 2

        for sub in all_subs:
            if sub.plan.level == 10:
                assert sub.status == SubscriptionStatus.Paused
            else:
                assert sub.status == SubscriptionStatus.Active


@pytest.mark.asyncio
async def test_create_subscription_with_the_same_plan():
    # Before
    auth_user = AuthUser()
    subscriber_id = "AnySubId"
    personal_plan = create_plan(title="Business", level=20, auth_user=auth_user)
    first_sub = create_subscription(plan=personal_plan, subscriber_id=subscriber_id, auth_user=auth_user)

    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(first_sub)
        await uow.commit()

    # Test
    second_sub = create_subscription(plan=personal_plan, subscriber_id=subscriber_id, auth_user=auth_user)

    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        service = SubscriptionService(bus, uow)
        await service.create_one(second_sub)
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
        self.plan = Plan(
            title="Personal",
            price=100,
            currency="USD",
            billing_cycle=Cycle.from_code(CycleCode.Monthly),
            level=10,
            auth_id=self.auth_user.id,
        )
        self.inferior_plan = Plan(
                title="Free",
                price=100,
                currency="USD",
                billing_cycle=Cycle.from_code(CycleCode.Monthly),
                level=1,
                auth_id=self.auth_user.id,
            )

    async def create_first_subscription(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription(subscriber_id=self.subscriber_id, plan=self.plan, auth_id=self.auth_user.id)
            await SubscriptionService(container.eventbus(), uow).create_one(subscription)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_one_by_id(subscription.id)
            assert real.status == SubscriptionStatus.Active

    async def create_second_subscription_with_the_same_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription(subscriber_id=self.subscriber_id, plan=self.plan, auth_id=self.auth_user.id)
            await SubscriptionService(container.eventbus(), uow).create_one(subscription)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.subscription_repo().get_one_by_id(subscription.id)
            assert real.status == SubscriptionStatus.Paused

    async def create_third_subscription_with_superior_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            superior_plan = Plan(
                title="Business",
                price=100,
                currency="USD",
                billing_cycle=Cycle.from_code(CycleCode.Monthly),
                level=20,
                auth_id=self.auth_user.id,
            )
            subscription = Subscription(subscriber_id=self.subscriber_id, plan=superior_plan, auth_id=self.auth_user.id)
            await SubscriptionService(container.eventbus(), uow).create_one(subscription)
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
            subscription = Subscription(
                subscriber_id=self.subscriber_id, plan=self.inferior_plan, auth_id=self.auth_user.id
            )
            await SubscriptionService(container.eventbus(), uow).create_one(subscription)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            subs = await uow.subscription_repo().get_selected(SubscriptionSby())
            assert len(subs) == 4
            for sub in subs:
                if sub.plan.level == 20:
                    assert sub.status == SubscriptionStatus.Active
                else:
                    assert sub.status == SubscriptionStatus.Paused

    async def test_create_fifth_subscription_with_inferior_plan(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            subscription = Subscription(
                subscriber_id=self.subscriber_id, plan=self.inferior_plan, auth_id=self.auth_user.id
            )
            await SubscriptionService(container.eventbus(), uow).create_one(subscription)
            await uow.commit()

        async with container.unit_of_work_factory().create_uow() as uow:
            subs = await uow.subscription_repo().get_selected(SubscriptionSby())
            assert len(subs) == 5
            for sub in subs:
                if sub.plan.level == 20:
                    assert sub.status == SubscriptionStatus.Active
                else:
                    assert sub.status == SubscriptionStatus.Paused

    @pytest.mark.asyncio
    async def test_foo(self):
        await self.create_first_subscription()
        await self.create_second_subscription_with_the_same_plan()
        await self.create_third_subscription_with_superior_plan()
        await self.create_forth_subscription_with_inferior_plan()
        await self.test_create_fifth_subscription_with_inferior_plan()
