import pytest

from backend.bootstrap import get_container
from backend.subscription.domain.subscription_repo import SubscriptionSby
from tests.fake_data import create_subscription

container = get_container()


@pytest.mark.asyncio
async def test_create_one():
    async with container.unit_of_work_factory().create_uow() as uow:
        item = create_subscription()

        await uow.subscription_repo().add_one(item)
        with pytest.raises(LookupError):
            await uow.subscription_repo().get_one_by_id(item.id)

        await uow.commit()
        await uow.subscription_repo().get_one_by_id(item.id)

        await uow.rollback()
        with pytest.raises(LookupError):
            await uow.subscription_repo().get_one_by_id(item.id)


@pytest.mark.asyncio
async def test_create_many():
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [create_subscription() for _ in range(11)]

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
async def test_update_one():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = create_subscription()
        await uow.subscription_repo().add_one(item)
        await uow.commit()

    # Test
    async with container.unit_of_work_factory().create_uow() as uow:
        updated = item.shift_last_billing(10)

        # Update without commit
        await uow.subscription_repo().update_one(updated)
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.expiration_date == item.expiration_date

        # Commit
        await uow.commit()
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.expiration_date == updated.expiration_date

        # Rollback
        await uow.rollback()
        real = await uow.subscription_repo().get_one_by_id(item.id)
        assert real.expiration_date == item.expiration_date


@pytest.mark.asyncio
async def test_delete_one():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = create_subscription()
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
async def test_delete_many():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [create_subscription() for _ in range(11)]
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
