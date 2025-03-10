from loguru import logger

from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.shared.utils.dt import get_current_datetime
from backend.subscription.application.subscription_usecases import save_updated_subscription
from backend.subscription.domain.enums import SubscriptionStatus
from backend.subscription.domain.subscription import Subscription
from backend.subscription.domain.subscription_repo import SubscriptionSby


class SubManager:
    def __init__(self, uow_factory: UnitOfWorkFactory, bulk_limit=100):
        self._uow_factory = uow_factory
        self._bulk_limit = bulk_limit

    @staticmethod
    async def _processing_expired_sub(sub: Subscription, uow: UnitOfWork):
        try:
            sub.expire()
            await save_updated_subscription(sub, uow)
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
                other_sub.resume()
                await save_updated_subscription(other_sub, uow)
        except Exception as err:
            logger.exception(err)

    async def manage_expired_subscriptions(self):
        while True:
            async with self._uow_factory.create_uow() as uow:
                sby = SubscriptionSby(
                    statuses={SubscriptionStatus.Active},
                    expiration_date_lt=get_current_datetime(),
                    limit=self._bulk_limit,
                )
                expired_subscriptions = await uow.subscription_repo().get_selected(sby)
                if len(expired_subscriptions) == 0:
                    break

                logger.info(f"{len(expired_subscriptions)} active subscriptions needed to change status into expired")
                for sub in expired_subscriptions:
                    await self._processing_expired_sub(sub, uow)

                await uow.commit()

    async def manage_usages(self):
        while True:
            async with self._uow_factory.create_uow() as uow:
                targets = await uow.subscription_repo().get_selected(
                    SubscriptionSby(
                        usage_renew_date_lt=get_current_datetime(),
                        limit=self._bulk_limit,
                    )
                )
                if len(targets) == 0:
                    break

                logger.info(f"{len(targets)} subscriptions needed to renew usages")
                for target in targets:
                    for usage in target.usages:
                        if usage.need_to_renew:
                            usage.renew()
                    await save_updated_subscription(target, uow)
                await uow.commit()

    async def manage(self):
        logger.info("Managing subscriptions")
        await self.manage_expired_subscriptions()
        await self.manage_usages()
