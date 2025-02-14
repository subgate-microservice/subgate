from typing import Iterable

from pydantic import AwareDatetime

from backend.shared.context import Context
from backend.shared.eventbus import Eventbus, Event
from backend.shared.events import EventCode
from backend.shared.unit_of_work.uow import UnitOfWork
from backend.subscription.domain.plan import UsageOld, Plan
from backend.subscription.domain.subscription import Subscription, SubscriptionStatus, SubId
from backend.subscription.domain.subscription_repo import SubscriptionSby


class BaseService:
    def __init__(
            self,
            bus: Eventbus,
            uow: UnitOfWork,
    ):
        self._bus = bus
        self._uow = uow
        self._events: list[Event] = []

    def _add_event(self, code: EventCode, payload: Subscription):
        self._events.append(Event(code=code, payload=payload, context=Context(uow=self._uow)))

    async def send_events(self):
        for event in self._events:
            await self._bus.publish(event)
        self._events = []


class SubscriptionPartialUpdateService(BaseService):
    async def pause_sub(self, sub: Subscription) -> None:
        if sub.status != SubscriptionStatus.Paused:
            result = sub.pause()
            await self._uow.subscription_repo().update_one(result)
            self._add_event(EventCode.SubscriptionUpdated, result)
            self._add_event(EventCode.SubscriptionPaused, result)

    async def resume_sub(self, sub: Subscription) -> None:
        result = sub.resume()
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)
        self._add_event(EventCode.SubscriptionResumed, result)

    async def renew_sub(self, sub: Subscription, from_date: AwareDatetime = None) -> None:
        result = sub.renew(from_date)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)
        self._add_event(EventCode.SubscriptionRenewed, result)

    async def expire_sub(self, sub: Subscription) -> None:
        result = sub.expire()
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)
        self._add_event(EventCode.SubscriptionExpired, result)

    async def shift_last_billing(self, sub: Subscription, days: int) -> None:
        result = sub.shift_last_billing(days)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)
        self._add_event(EventCode.LastBillingChanged, result)

    async def increase_usage(self, sub: Subscription, resource: str, delta: float) -> None:
        result = sub.increase_usage(resource, delta)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)

    async def add_usages(self, sub: Subscription, usages: Iterable[UsageOld]) -> None:
        result = sub.add_usages(usages)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)

    async def remove_usages(self, sub: Subscription, resources: Iterable[str]) -> None:
        result = sub.remove_usages(resources)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)

    async def update_usages(self, sub: Subscription, usages: Iterable[UsageOld]) -> None:
        result = sub.update_usages(usages)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)

    async def update_plan(self, sub: Subscription, plan: Plan) -> None:
        result = sub.update_plan(plan)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)


class SubscriptionService(BaseService):
    def __init__(self, bus: Eventbus, uow: UnitOfWork):
        super().__init__(bus, uow)
        self._partial_service = SubscriptionPartialUpdateService(bus, uow)

    async def create_one(self, item: Subscription):
        subscriber_active_sub = await self._uow.subscription_repo().get_subscriber_active_one(
            subscriber_id=item.subscriber_id, auth_id=item.auth_id,
        )

        if subscriber_active_sub:
            # Если создаваемая подписка старше активной, то ставим на паузу активную подписку
            if item.plan_info.level > subscriber_active_sub.plan_info.level:
                await self._partial_service.pause_sub(subscriber_active_sub)
            # Если создаваемая подписка идентична или младше активной, то ставим создаваемую подписку на паузу
            else:
                item = item.pause()

        await self._uow.subscription_repo().add_one(item)
        self._add_event(EventCode.SubscriptionCreated, item)

    async def update_one(self, sub: Subscription) -> None:
        await self._uow.subscription_repo().update_one(sub)
        self._add_event(EventCode.SubscriptionUpdated, sub)

    async def delete_one(self, sub: Subscription) -> None:
        await self._uow.subscription_repo().delete_many([sub])
        self._add_event(EventCode.SubscriptionDeleted, sub)

    async def delete_selected(self, sby: SubscriptionSby) -> None:
        targets = await self._uow.subscription_repo().get_selected(sby)
        await self._uow.subscription_repo().delete_many(targets)
        for target in targets:
            self._add_event(EventCode.SubscriptionDeleted, target)

    async def send_events(self):
        await super().send_events()
        await self._partial_service.send_events()


async def create_subscription(item: Subscription, uow: UnitOfWork) -> None:
    current_sub = await uow.subscription_repo().get_subscriber_active_one(
        subscriber_id=item.subscriber_id, auth_id=item.auth_id,
    )

    if current_sub:
        # Если создаваемая подписка старше текущей, то ставим на паузу текущую подписку
        if item.plan_info.level > current_sub.plan_info.level:
            new_version = current_sub.copy()
            new_version.pause()
            await update_subscription(current_sub, new_version, uow)
        # Если создаваемая подписка идентична или младше текущей, то ставим создаваемую подписку на паузу
        else:
            item.pause()

    await uow.subscription_repo().add_one(item)


async def update_subscription(old_sub: Subscription, new_sub: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().update_one(new_sub)
