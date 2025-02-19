from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.events import SubscriptionDeleted
from backend.subscription.domain.subscription import (
    Subscription, )
from backend.subscription.domain.subscription_services import SubscriptionUpdatesEventGenerator, SubscriptionEventParser


async def create_subscription(new_sub: Subscription, uow: UnitOfWork) -> None:
    current_sub = await uow.subscription_repo().get_subscriber_active_one(
        subscriber_id=new_sub.subscriber_id, auth_id=new_sub.auth_id,
    )

    if current_sub:
        # Если создаваемая подписка старше текущей, то ставим на паузу текущую подписку
        if new_sub.plan_info.level > current_sub.plan_info.level:
            current_sub.pause()
            await save_updated_subscription(current_sub, uow)
        # Если создаваемая подписка идентична или младше текущей, то ставим создаваемую подписку на паузу
        else:
            new_sub.pause()

    await uow.subscription_repo().add_one(new_sub)


async def update_subscription_from_another(old_sub: Subscription, new_sub: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().update_one(new_sub)
    events = SubscriptionUpdatesEventGenerator(old_sub, new_sub).generate_events()
    for ev in events:
        uow.push_event(ev)


async def save_updated_subscription(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().update_one(target)
    events = SubscriptionEventParser(target).parse(target.parse_events())
    for ev in events:
        uow.push_event(ev)


async def delete_subscription(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().delete_many([target])
    event = SubscriptionDeleted(subscription_id=target.id, auth_id=target.auth_id, occurred_at=get_current_datetime())
    uow.push_event(event)
