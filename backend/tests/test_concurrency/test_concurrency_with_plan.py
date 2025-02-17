import asyncio

import pytest

from backend.bootstrap import container
from tests.fakes import simple_plan


@pytest.mark.asyncio
async def test_concurrency_with_update(simple_plan):
    plan = simple_plan

    async def first_started_second_finished():
        async with container.unit_of_work_factory().create_uow() as uw:
            target = await uw.plan_repo().get_one_by_id(plan.id)
            await asyncio.sleep(1)
            target.price = 222
            await uw.plan_repo().update_one(target)
            await uw.commit()

    async def second_started_first_finished():
        await asyncio.sleep(0.5)
        async with container.unit_of_work_factory().create_uow() as uw:
            target = await uw.plan_repo().get_one_by_id(plan.id)
            target.title = "Updated"
            await uw.plan_repo().update_one(target)
            await uw.commit()

    task1 = first_started_second_finished()
    task2 = second_started_first_finished()
    await asyncio.gather(task1, task2)

    async with container.unit_of_work_factory().create_uow() as uow:
        real = await uow.plan_repo().get_one_by_id(plan.id)
        assert real.price == 222
        assert real.title == "Updated"
