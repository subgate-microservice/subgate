from backend.shared.unit_of_work.uow import UnitOfWork
from backend.subscription.domain.events import SubDeleted, SubCreated
from backend.subscription.domain.subscription import (
    Subscription, )
from backend.subscription.domain.subscription_services import SubscriptionEventParser, SubscriptionUpdater


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
    uow.push_event(
        SubCreated(
            id=new_sub.id,
            subscriber_id=new_sub.subscriber_id,
            status=new_sub.status,
            price=new_sub.billing_info.price,
            currency=new_sub.billing_info.currency,
            billing_cycle=new_sub.billing_info.billing_cycle,
            auth_id=new_sub.auth_id

        )
    )
    await uow.subscription_repo().add_one(new_sub)


async def update_subscription_from_another(target_sub: Subscription, new_sub: Subscription, uow: UnitOfWork) -> None:
    SubscriptionUpdater(target_sub).update(new_sub)
    await save_updated_subscription(target_sub, uow)


async def save_updated_subscription(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().update_one(target)
    events = SubscriptionEventParser(target).parse(target.parse_events())
    for ev in events:
        uow.push_event(ev)


async def delete_subscription(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().delete_many([target])
    event = SubDeleted(
        id=target.id,
        subscriber_id=target.subscriber_id,
        status=target.status,
        price=target.billing_info.price,
        currency=target.billing_info.currency,
        billing_cycle=target.billing_info.billing_cycle,
        auth_id=target.auth_id
    )
    uow.push_event(event)
