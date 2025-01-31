import asyncio

import pytest

from backend.bootstrap import container
from tests.fake_data import create_plan


@pytest.mark.asyncio
async def test_concurrency_with_update():
    # Before
    plan = create_plan()
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(plan)
        await uow.commit()

    # Test
    async def first_started_second_finished():
        async with container.unit_of_work_factory().create_uow() as uw:
            target = await uw.plan_repo().get_one_by_id(plan.id)
            await asyncio.sleep(1)
            updated = target.model_copy(update={"price": 222})
            await uw.plan_repo().update_one(updated)
            await uw.commit()

    async def second_started_first_finished():
        await asyncio.sleep(0.5)
        async with container.unit_of_work_factory().create_uow() as uw:
            target = await uw.plan_repo().get_one_by_id(plan.id)
            updated = target.model_copy(update={"title": "Updated"})
            await uw.plan_repo().update_one(updated)
            await uw.commit()

    task1 = first_started_second_finished()
    task2 = second_started_first_finished()
    await asyncio.gather(task1, task2)

    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.plan_repo().get_one_by_id(plan.id)
        assert real.price == 222
        assert real.title == "Updated"
