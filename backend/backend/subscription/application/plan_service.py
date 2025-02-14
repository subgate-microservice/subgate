from backend.shared.unit_of_work.uow import UnitOfWork
from backend.subscription.domain.plan import Plan, PlanEventFactory


async def create_plan(plan: Plan, uow: UnitOfWork) -> None:
    await uow.plan_repo().add_one(plan)
    event = PlanEventFactory(plan).plan_created()
    uow.push_event(event)


async def delete_plan(plan: Plan, uow: UnitOfWork) -> None:
    await uow.plan_repo().delete_one(plan)
    event = PlanEventFactory(plan).plan_deleted()
    uow.push_event(event)


async def update_plan(old_plan: Plan, new_plan: Plan, uow: UnitOfWork) -> None:
    await uow.plan_repo().update_one(new_plan)
    event = PlanEventFactory(old_plan).plan_updated(new_plan)
    uow.push_event(event)
