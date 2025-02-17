from uuid import uuid4

import pytest

from backend.bootstrap import get_container
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.plan_repo import PlanSby

container = get_container()


@pytest.mark.asyncio
async def test_create_one():
    async with container.unit_of_work_factory().create_uow() as uow:
        item = Plan("Personal", 100, "USD", uuid4())
        await uow.plan_repo().add_one(item)

        # Без коммита данных нет в базе
        with pytest.raises(LookupError):
            await uow.plan_repo().get_one_by_id(item.id)

        # После коммита данные появились
        await uow.commit()
        await uow.plan_repo().get_one_by_id(item.id)

        # После отката снова ушли
        await uow.rollback()
        with pytest.raises(LookupError):
            await uow.plan_repo().get_one_by_id(item.id)


@pytest.mark.asyncio
async def test_create_many():
    async with container.unit_of_work_factory().create_uow() as uow:
        # Без коммита данных нет в базе
        items = [Plan("Personal", 100, "USD", uuid4()) for _ in range(11)]
        await uow.plan_repo().add_many(items)
        real = await uow.plan_repo().get_selected(PlanSby())
        assert len(real) == 0

        # После коммита данные появились
        await uow.commit()
        real = await uow.plan_repo().get_selected(PlanSby())
        assert len(real) == len(items)

        # После отката снова ушли
        await uow.rollback()
        real = await uow.plan_repo().get_selected(PlanSby())
        assert len(real) == 0


@pytest.mark.asyncio
async def test_update_one():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = Plan("Personal", 100, "USD", uuid4())
        await uow.plan_repo().add_one(item)
        await uow.commit()

    # Test
    updated = item.copy()
    updated.price = 123_123

    async with container.unit_of_work_factory().create_uow() as uow:
        # Update without commit
        await uow.plan_repo().update_one(updated)
        real = await uow.plan_repo().get_one_by_id(item.id)
        assert real.price == item.price

        # Commit
        await uow.commit()
        real = await uow.plan_repo().get_one_by_id(item.id)
        assert real.price == updated.price

        # Rollback
        await uow.rollback()
        real = await uow.plan_repo().get_one_by_id(item.id)
        assert real.price == item.price


@pytest.mark.asyncio
async def test_delete_one():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = Plan("Personal", 100, "USD", uuid4())
        await uow.plan_repo().add_one(item)
        await uow.commit()

    async with container.unit_of_work_factory().create_uow() as uow:
        # Test without commit
        target = await uow.plan_repo().get_one_by_id(item.id)
        await uow.plan_repo().delete_one(target)
        real = await uow.plan_repo().get_one_by_id(item.id)
        assert real.id == item.id

        # Test with commit
        await uow.commit()
        with pytest.raises(LookupError):
            _ = await uow.plan_repo().get_one_by_id(item.id)

        # Test with rollback
        await uow.rollback()
        real = await uow.plan_repo().get_one_by_id(item.id)
        assert real.id == item.id


@pytest.mark.asyncio
async def test_delete_many():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [Plan("Personal", 100, "USD", uuid4()) for _ in range(11)]
        await uow.plan_repo().add_many(items)
        await uow.commit()

    # Test without commit
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().delete_many(items)
        real = await uow.plan_repo().get_selected(PlanSby())
        assert len(real) == len(items)

        # Test with commit
        await uow.commit()
        real = await uow.plan_repo().get_selected(PlanSby())
        assert len(real) == 0

        # Test with rollback
        await uow.rollback()
        real = await uow.plan_repo().get_selected(PlanSby())
        assert len(real) == len(items)
