from backend.shared.unit_of_work.uow import UnitOfWork
from backend.subscription.domain.events import PlanCreated, PlanDeleted
from backend.subscription.domain.plan import Plan, PlanEventParser


async def create_plan(plan: Plan, uow: UnitOfWork) -> None:
    await uow.plan_repo().add_one(plan)
    event = PlanCreated(
        id=plan.id,
        title=plan.title,
        price=plan.price,
        currency=plan.currency,
        billing_cycle=plan.billing_cycle,
        auth_id=plan.auth_id,
    )
    uow.push_event(event)


async def delete_plan(plan: Plan, uow: UnitOfWork) -> None:
    await uow.plan_repo().delete_one(plan)
    event = PlanDeleted(
        id=plan.id,
        title=plan.title,
        price=plan.price,
        currency=plan.currency,
        billing_cycle=plan.billing_cycle,
        auth_id=plan.auth_id,
    )
    uow.push_event(event)


async def save_updated_plan(plan: Plan, uow: UnitOfWork) -> None:
    await uow.plan_repo().update_one(plan)
    events = plan.parse_events()
    events = PlanEventParser(plan).parse(events)
    for ev in events:
        uow.push_event(ev)
