from typing import Callable

from loguru import logger

from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.shared.utils import get_current_datetime
from backend.subscription.application.subscription_service import (expire_subscription, resume_subscription,
                                                                   renew_subscription, renew_subscription_usages)
from backend.subscription.domain.subscription import SubscriptionStatus, Subscription
from backend.subscription.domain.subscription_repo import SubscriptionSby


class SubManager:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    @staticmethod
    async def _processing_expired_sub(sub: Subscription, uow: UnitOfWork):
        try:
            await expire_subscription(sub, uow)
            # Если есть подписка на паузе, то возобновляем
            sby = SubscriptionSby(
                statuses={SubscriptionStatus.Paused},
                subscriber_ids={sub.subscriber_id},
                order_by=[("plan_info.level", -1)],
                auth_ids={sub.auth_id},
                limit=1,
            )
            other_subscriber_subs = await uow.subscription_repo().get_selected(sby)
            for other_sub in other_subscriber_subs:
                await resume_subscription(other_sub, uow)
        except Exception as err:
            logger.exception(err)

    @staticmethod
    async def _processing_autorenew_sub(sub: Subscription, uow: UnitOfWork):
        await renew_subscription(sub, uow)

    async def manage_expired_subscriptions(self):
        async with self._uow_factory.create_uow() as uow:
            sby = SubscriptionSby(
                statuses={SubscriptionStatus.Active},
                expiration_date_lt=get_current_datetime(),
                limit=100,
            )
            expired_subscriptions = await uow.subscription_repo().get_selected(sby)
            logger.info(f"{len(expired_subscriptions)} active subscriptions needed to change status into expired")
            for sub in expired_subscriptions:
                processor: Callable = self._processing_autorenew_sub if sub.autorenew else self._processing_expired_sub
                await processor(sub, uow)

            await uow.commit()

    async def manage_usages(self):
        async with self._uow_factory.create_uow() as uow:
            targets = await uow.subscription_repo().get_selected(
                SubscriptionSby(
                    usage_renew_date_lt=get_current_datetime()
                )
            )
            logger.info(f"{len(targets)} subscriptions needed to renew usages")
            for target in targets:
                await renew_subscription_usages(target, uow)
            await uow.commit()
