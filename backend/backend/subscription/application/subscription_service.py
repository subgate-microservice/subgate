from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.subscription import (
    Subscription, SubscriptionUpdatesEventGenerator, SubscriptionDeleted, )


class SubscriptionPartialUpdateService:
    pass


class SubscriptionService:
    pass


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
    events = SubscriptionUpdatesEventGenerator(old_sub, new_sub).generate_events()
    for ev in events:
        uow.push_event(ev)


async def update_subscription_new(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().update_one(target)
    events = target.parse_events()
    for ev in events:
        uow.push_event(ev)


async def delete_subscription(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().delete_many([target])
    event = SubscriptionDeleted(subscription_id=target.id, auth_id=target.auth_id, occurred_at=get_current_datetime())
    uow.push_event(event)
