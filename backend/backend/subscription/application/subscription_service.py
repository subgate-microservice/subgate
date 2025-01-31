from typing import Iterable

from pydantic import AwareDatetime

from backend.shared.context import Context
from backend.shared.eventbus import Eventbus, Event
from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.events import EventCode
from backend.subscription.domain.plan import Usage, Plan
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

    async def add_usages(self, sub: Subscription, usages: Iterable[Usage]) -> None:
        result = sub.add_usages(usages)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)

    async def remove_usages(self, sub: Subscription, resources: Iterable[str]) -> None:
        result = sub.remove_usages(resources)
        await self._uow.subscription_repo().update_one(result)
        self._add_event(EventCode.SubscriptionUpdated, result)

    async def update_usages(self, sub: Subscription, usages: Iterable[Usage]) -> None:
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
        created_sub = item
        if created_sub.status != SubscriptionStatus.Active:
            raise ValueError(f"You are trying create subscription with {created_sub.status} status")
        subscriber_active_sub = await self._uow.subscription_repo().get_subscriber_active_one(
            subscriber_id=created_sub.subscriber_id, auth_id=created_sub.auth_id,
        )

        if subscriber_active_sub:
            # Если создаваемая подписка старше активной
            if created_sub.plan.level > subscriber_active_sub.plan.level:
                # Ставим на паузу активную подписку
                await self._partial_service.pause_sub(subscriber_active_sub)

                # Создаем новую подписку
                await self._uow.subscription_repo().add_one(created_sub)
                self._add_event(EventCode.SubscriptionCreated, created_sub)

            # Если создаваемая подписка идентична активной, то ставим создаваемую подписку на паузу
            elif created_sub.plan.level == subscriber_active_sub.plan.level:
                created_sub = created_sub.pause()
                await self._uow.subscription_repo().add_one(created_sub)
                self._add_event(EventCode.SubscriptionCreated, created_sub)

            # Если создаваемая подписка младше активной
            elif created_sub.plan.level < subscriber_active_sub.plan.level:
                sby = SubscriptionSby(subscriber_ids={created_sub.subscriber_id})

                # Пытаемся найти подписки с идентичным планом
                # Если такие есть, то мы их продлеваем
                # Если таких нет, то мы просто создаем новую подписку и ставим ее на паузу
                other_subs = await self._uow.subscription_repo().get_selected(sby)
                try:
                    target = next(x for x in other_subs if created_sub.plan.level == x.plan.level)
                    await self._partial_service.shift_last_billing(target, created_sub.days_left)
                except StopIteration:
                    created_sub = created_sub.pause()
                    await self._uow.subscription_repo().add_one(created_sub)
                    self._add_event(EventCode.SubscriptionCreated, created_sub)
        else:
            await self._uow.subscription_repo().add_one(item)
            self._add_event(EventCode.SubscriptionCreated, item)

    async def get_one_by_id(self, sub_id: SubId) -> Subscription:
        result = await self._uow.subscription_repo().get_one_by_id(sub_id)
        return result

    async def get_selected(self, sby: SubscriptionSby) -> list[Subscription]:
        return await self._uow.subscription_repo().get_selected(sby)

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
