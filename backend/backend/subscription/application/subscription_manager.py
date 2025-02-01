import asyncio
import traceback
from typing import Callable

from loguru import logger

from backend.shared.context import Context
from backend.shared.eventbus import Eventbus, Event
from backend.shared.events import EventCode
from backend.shared.unit_of_work.uow import UnitOfWorkFactory
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.subscription import SubscriptionStatus, Subscription
from backend.subscription.domain.subscription_repo import SubscriptionSby


class BaseManager:
    def __init__(
            self,
            uow_factory: UnitOfWorkFactory,
            bus: Eventbus,
    ):
        self._uow_factory = uow_factory
        self._bus = bus
        self._events: list[Event] = []

    async def _send_events(self):
        for event in self._events:
            await self._bus.publish(event)
        self._events = []


class SubscriptionManager(BaseManager):
    async def _processing_expired_sub(self, sub: Subscription):
        try:
            async with self._uow_factory.create_uow() as uow:
                # Работаем с истекшей подпиской
                sub = sub.expire()
                await uow.subscription_repo().update_one(sub)
                self._events.append(Event(EventCode.SubscriptionExpired, sub, Context(uow=uow)))

                # Если есть подписка на паузе, то возобновляем
                sby = SubscriptionSby(
                    statuses={SubscriptionStatus.Paused},
                    subscriber_ids={sub.subscriber_id},
                    order_by=[("plan.level", -1)],
                    auth_ids={sub.auth_id},
                    limit=1,
                )
                other_subscriber_subs = await uow.subscription_repo().get_selected(sby)
                for other_sub in other_subscriber_subs:
                    other_sub = other_sub.resume()
                    await uow.subscription_repo().update_one(other_sub)
                    self._events.append(Event(EventCode.SubscriptionResumed, other_sub, Context(uow=uow)))
                    await self._send_events()
                await uow.commit()
        except Exception as err:
            traceback.print_exception(err)

    async def _processing_autorenew_sub(self, sub: Subscription):
        try:
            async with self._uow_factory.create_uow() as uow:
                sub = sub.renew()
                await uow.subscription_repo().update_one(sub)
                self._events.append(Event(EventCode.SubscriptionRenewed, sub, Context(uow=uow)))
                await self._send_events()
                await uow.commit()

        except Exception as err:
            traceback.print_exception(err)

    async def manage_expired_subscriptions(self):
        async with self._uow_factory.create_uow() as uow:
            sby = SubscriptionSby(
                statuses={SubscriptionStatus.Active},
                expiration_date_lt=get_current_datetime(),
                limit=10_000,
            )
            expired_subscriptions = await uow.subscription_repo().get_selected(sby)
            logger.info(f"{len(expired_subscriptions)} active subscriptions needed to change status into expired")

        tasks = []
        for sub in expired_subscriptions:
            processor: Callable = self._processing_autorenew_sub if sub.autorenew else self._processing_expired_sub
            task = asyncio.create_task(processor(sub))
            task.set_name(f"Processing expired subscription (id={sub.id})")
            tasks.append(task)
        await asyncio.gather(*tasks)


class SubscriptionUsageManager(BaseManager):

    async def _update_usages_in_subscription(self, sub: Subscription):
        try:
            # Подготавливаем данные (обновляем Usages)
            updated_usages = []
            for usage in sub.usages:
                if usage.need_to_renew:
                    usage = usage.renew()
                    updated_usages.append(usage)
                else:
                    updated_usages.append(usage)
            sub = sub.update_usages(updated_usages)

            async with self._uow_factory.create_uow() as uow:
                await uow.subscription_repo().update_one(sub)
                self._events.append(Event(EventCode.SubscriptionUpdated, sub, Context(uow=uow)))
                await self._send_events()
                await uow.commit()

        except Exception as err:
            traceback.print_exception(err)

    async def manage_usages(self):
        async with self._uow_factory.create_uow() as uow:
            targets = await uow.subscription_repo().get_selected(
                SubscriptionSby(
                    usage_renew_date_lt=get_current_datetime()
                )
            )
            logger.info(f"{len(targets)} subscriptions needed to renew usages")

        tasks = []
        for sub in targets:
            task = asyncio.create_task(self._update_usages_in_subscription(sub))
            task.set_name(f"Update usages in subscription (id={sub.id})")
            tasks.append(task)
        await asyncio.gather(*tasks)
