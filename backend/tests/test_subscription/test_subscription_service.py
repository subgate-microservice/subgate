import pytest

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.subscription.application.subscription_service import SubscriptionService
from backend.subscription.domain.subscription import SubscriptionStatus
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

# class TestIncreaseSubscriptionUsage:
#     @pytest.mark.asyncio
#     async def test_with_concurrency(self):
#         # Before
#         usages = [
#             Usage(
#                 resource="first", unit="GB", available_units=100, used_units=0,
#                 renew_cycle=Cycle.from_code(CycleCode.Monthly))
#         ]
#         sub = create_subscription(usages=usages)
#         async with container.unit_of_work_factory().create_uow() as uow:
#             await uow.subscription_repo().add_one(sub)
#
#         async def update_usage_task():
#             async with container.unit_of_work_factory().create_uow() as uw:
#                 service = SubscriptionPartialUpdateService(container.eventbus(), uw)
#                 await service.increase_usage(sub, "first", 20)
#
#         coros = [update_usage_task() for _ in range(0, 1000)]
#         await asyncio.gather(*coros)
#
#         real = await container.unit_of_work_factory().create_uow().subscription_repo().get_one_by_id(sub.id)
#         assert real.usages[0].used_units == 20 * len(coros)
#
