import math

from backend.shared.context import Context
from backend.shared.eventbus import Eventbus, Event
from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.events import EventCode
from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.plan_repo import PlanSby


class BaseService:
    def __init__(
            self,
            bus: Eventbus,
            uow: UnitOfWork,
    ):
        self._bus = bus
        self._uow = uow
        self._events: list[Event] = []

    def _plan_created(self, plan: Plan):
        self._events.append(
            Event(
                code=EventCode.PlanCreated,
                payload=plan,
                context=Context(uow=self._uow),
            )
        )

    def _plan_updated(self, plan: Plan):
        self._events.append(
            Event(
                code=EventCode.PlanUpdated,
                payload=plan,
                context=Context(uow=self._uow),
            )
        )

    def _plan_deleted(self, plan: Plan):
        self._events.append(
            Event(
                code=EventCode.PlanDeleted,
                payload=plan,
                context=Context(uow=self._uow),
            )
        )

    async def _send_events(self):
        for event in self._events:
            await self._bus.publish(event)
        self._events = []


class PlanService(BaseService):
    async def create_one(self, plan: Plan) -> None:
        await self._uow.plan_repo().add_one(plan)
        self._plan_created(plan)
        await self._send_events()

    async def get_one_by_id(self, plan_id: PlanId) -> Plan:
        return await self._uow.plan_repo().get_one_by_id(plan_id)

    async def get_selected(self, sby: PlanSby) -> list[Plan]:
        return await self._uow.plan_repo().get_selected(sby)

    async def update_one(self, plan: Plan) -> None:
        await self._uow.plan_repo().update_one(plan)
        self._plan_updated(plan)
        await self._send_events()

    async def delete_one(self, plan: Plan) -> None:
        await self._uow.plan_repo().delete_one(plan)
        self._plan_deleted(plan)
        await self._send_events()

    async def delete_selected(self, sby: PlanSby) -> None:
        targets = await self._uow.plan_repo().get_selected(sby)
        await self._uow.plan_repo().delete_many(targets)
        for target in targets:
            self._plan_deleted(target)
        await self._send_events()


def check_amount_is_correct(plan: Plan, amount: float) -> None:
    if not math.isclose(plan.price, amount):
        raise ValueError(f"Amount is not equal Plan.price (f{amount} != {plan.price})")
