import pytest

from backend.bootstrap import get_container
from backend.subscription.domain.plan import Plan
from tests.conftest import current_user

container = get_container()


@pytest.mark.asyncio
async def test_uow_without_commit_does_not_change_state(current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = Plan("Business", 111, "USD", current_user.id)
        await uow.plan_repo().add_one(plan)

        with pytest.raises(LookupError):
            await uow.plan_repo().get_one_by_id(plan.id)


@pytest.mark.asyncio
async def test_uow_with_commit_changes_state(current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = Plan("Business", 111, "USD", current_user.id)
        await uow.plan_repo().add_one(plan)
        await uow.commit()

        await uow.plan_repo().get_one_by_id(plan.id)


@pytest.mark.asyncio
async def test_uow_with_rollback_does_not_change_state(current_user):
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = Plan("Business", 111, "USD", current_user.id)

        await uow.plan_repo().add_one(plan)
        await uow.plan_repo().add_one(plan)
        with pytest.raises(Exception):
            await uow.commit()

        await uow.rollback()
        with pytest.raises(LookupError):
            await uow.plan_repo().get_one_by_id(plan.id)
