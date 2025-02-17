from datetime import timedelta

import pytest

from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.subscription import Subscription
from backend.subscription.domain.subscription_repo import SubscriptionSby
from tests.fakes import simple_plan

container = get_container()


@pytest.mark.asyncio
async def test_create_one(simple_plan):
    async with container.unit_of_work_factory().create_uow() as uow:
        item = Subscription.from_plan(simple_plan, "AnyID")

        await uow.subscription_repo().add_one(item)
        with pytest.raises(LookupError):
            await uow.subscription_repo().get_one_by_id(item.id)

        await uow.commit()
        await uow.subscription_repo().get_one_by_id(item.id)

        await uow.rollback()
        with pytest.raises(LookupError):
            await uow.subscription_repo().get_one_by_id(item.id)


@pytest.mark.asyncio
async def test_create_many(simple_plan):
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [Subscription.from_plan(simple_plan, "AnyID") for _ in range(11)]
        for item in items[1:]:
            item.pause()

        await uow.subscription_repo().add_many(items)
        real = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(real) == 0

        await uow.commit()
        real = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(real) == len(items)

        await uow.rollback()
        real = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(real) == 0


@pytest.mark.asyncio
async def test_update_one(simple_plan):
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = Subscription.from_plan(simple_plan, "AnyID")
        await uow.subscription_repo().add_one(item)
        await uow.commit()

    # Test
    async with container.unit_of_work_factory().create_uow() as uow:
        item.billing_info.last_billing = get_current_datetime() + timedelta(111)

        # Update without commit
        await uow.subscription_repo().update_one(item)
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.expiration_date != item.expiration_date

        # Commit
        await uow.commit()
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.expiration_date == item.expiration_date

        # Rollback
        await uow.rollback()
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.expiration_date != item.expiration_date


@pytest.mark.asyncio
async def test_delete_one(simple_plan):
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = Subscription.from_plan(simple_plan, "AnyID")
        await uow.subscription_repo().add_one(item)
        await uow.commit()

    # Test without commit
    async with container.unit_of_work_factory().create_uow() as uow:
        target = await uow.subscription_repo().get_one_by_id(item.id)
        await uow.subscription_repo().delete_one(target)
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.id == item.id

        # Test with commit
        await uow.commit()
        with pytest.raises(LookupError):
            _ = await uow.subscription_repo().get_one_by_id(item.id)

        # Test  with rollback
        await uow.rollback()
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.id == item.id


@pytest.mark.asyncio
async def test_delete_many(simple_plan):
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [Subscription.from_plan(simple_plan, "AnyID") for _ in range(11)]
        for item in items[1:]:
            item.pause()
        await uow.subscription_repo().add_many(items)
        await uow.commit()

    # Test without commit
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().delete_many(items)
        real = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(real) == len(items)

        # Test with commit
        await uow.commit()
        real = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(real) == 0

        # Test with rollback
        await uow.rollback()
        real = await uow.subscription_repo().get_selected(SubscriptionSby())
        assert len(real) == len(items)
