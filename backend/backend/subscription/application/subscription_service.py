from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.subscription import (
    Subscription, SubscriptionUpdatesEventGenerator, SubscriptionDeleted, SubscriptionUpdated, SubscriptionUsageUpdated,
    SubscriptionUsageAdded, SubscriptionUsageRemoved, SubscriptionDiscountAdded, SubscriptionDiscountRemoved,
    SubscriptionDiscountUpdated, SubscriptionStatus, SubscriptionResumed, SubscriptionExpired, SubscriptionRenewed,
)
from backend.subscription.domain.usage import Usage


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


async def delete_subscription(target: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().delete_many([target])
    event = SubscriptionDeleted(subscription_id=target.id, auth_id=target.auth_id, occurred_at=get_current_datetime())
    uow.push_event(event)


async def add_usage(target: Subscription, usage: Usage, uow: UnitOfWork) -> None:
    target.usages.add(usage)
    await uow.subscription_repo().update_one(target)

    usage = target.usages.get(usage.code)
    dt = get_current_datetime()

    subscription_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"usages.{usage.code}:added",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    subscription_usage_added = SubscriptionUsageAdded(
        subscription_id=target.id,
        code=usage.code,
        unit=usage.unit,
        available_units=usage.available_units,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(subscription_updated)
    uow.push_event(subscription_usage_added)


async def remove_usage(target: Subscription, code: str, uow: UnitOfWork) -> None:
    target.usages.remove(code)
    await uow.subscription_repo().update_one(target)

    dt = get_current_datetime()
    subscription_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"usages.{code}:removed",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    subscription_usage_removed = SubscriptionUsageRemoved(
        subscription_id=target.id,
        code=code,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(subscription_updated)
    uow.push_event(subscription_usage_removed)


async def update_usage(target: Subscription, usage: Usage, uow: UnitOfWork) -> None:
    dt = get_current_datetime()
    code = usage.code
    delta = usage.used_units - target.usages.get(code).available_units

    target.usages.update(usage)
    await uow.subscription_repo().update_one(target)

    subscription_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"usages.{usage.code}:updated",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )

    subscription_usage_updated = SubscriptionUsageUpdated(
        subscription_id=target.id,
        title=usage.title,
        code=usage.code,
        unit=usage.unit,
        available_units=usage.available_units,
        used_units=usage.used_units,
        delta=delta,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(subscription_updated)
    uow.push_event(subscription_usage_updated)


async def increase_usage(target: Subscription, code: str, value: float, uow: UnitOfWork) -> None:
    target.usages.get(code).increase(value)
    await uow.subscription_repo().update_one(target)

    usage = target.usages.get(code)
    dt = get_current_datetime()

    subscription_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"usages.{code}:updated",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )

    subscription_usage_updated = SubscriptionUsageUpdated(
        subscription_id=target.id,
        title=usage.title,
        code=usage.code,
        unit=usage.unit,
        available_units=usage.available_units,
        used_units=usage.used_units,
        delta=value,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(subscription_updated)
    uow.push_event(subscription_usage_updated)


async def add_discount(target: Subscription, discount: Discount, uow: UnitOfWork) -> None:
    dt = get_current_datetime()

    target.discounts.add(discount)
    await uow.subscription_repo().update_one(target)

    sub_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"discounts.{discount.code}:added",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )

    disc_added = SubscriptionDiscountAdded(
        subscription_id=target.subscriber_id,
        title=discount.title,
        code=discount.code,
        size=discount.size,
        valid_until=discount.valid_until,
        description=discount.description,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(sub_updated)
    uow.push_event(disc_added)


async def remove_discount(target: Subscription, code: str, uow: UnitOfWork) -> None:
    dt = get_current_datetime()

    target.discounts.remove(code)
    await uow.subscription_repo().update_one(target)

    sub_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"discounts.{code}:removed",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    disc_removed = SubscriptionDiscountRemoved(
        subscription_id=target.subscriber_id,
        code=code,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(sub_updated)
    uow.push_event(disc_removed)


async def update_discount(target: Subscription, discount: Discount, uow: UnitOfWork) -> None:
    dt = get_current_datetime()

    target.discounts.update(discount)
    await uow.subscription_repo().update_one(target)

    sub_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=(f"discounts.{discount.code}:updated",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    sub_discount_updated = SubscriptionDiscountUpdated(
        subscription_id=target.id,
        title=discount.title,
        code=discount.code,
        size=discount.size,
        valid_until=discount.valid_until,
        description=discount.description,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(sub_updated)
    uow.push_event(sub_discount_updated)


async def resume_subscription(target: Subscription, uow: UnitOfWork) -> None:
    dt = get_current_datetime()

    if target.status != SubscriptionStatus.Active:
        target.resume()
        await uow.subscription_repo().update_one(target)

        sub_updated = SubscriptionUpdated(
            subscription_id=target.id,
            changed_fields=("status", "paused_from"),
            auth_id=target.auth_id,
            occurred_at=dt,
        )

        sub_resumed = SubscriptionResumed(
            subscription_id=target.id,
            auth_id=target.auth_id,
            occurred_at=dt,
        )
        uow.push_event(sub_updated)
        uow.push_event(sub_resumed)


async def expire_subscription(target: Subscription, uow: UnitOfWork) -> None:
    dt = get_current_datetime()

    target.expire()
    await uow.subscription_repo().update_one(target)

    sub_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=("status",),
        auth_id=target.auth_id,
        occurred_at=dt,
    )

    sub_expired = SubscriptionExpired(
        subscription_id=target.id,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(sub_updated)
    uow.push_event(sub_expired)


async def renew_subscription(target: Subscription, uow: UnitOfWork) -> None:
    dt = get_current_datetime()

    target.renew()
    await uow.subscription_repo().update_one(target)

    sub_updated = SubscriptionUpdated(
        subscription_id=target.id,
        changed_fields=("status", "billing_info.last_billing", "paused_from"),
        auth_id=target.auth_id,
        occurred_at=dt,
    )

    sub_renewed = SubscriptionRenewed(
        subscription_id=target.id,
        last_billing=target.billing_info.last_billing,
        auth_id=target.auth_id,
        occurred_at=dt,
    )
    uow.push_event(sub_updated)
    uow.push_event(sub_renewed)


async def renew_subscription_usages(target: Subscription, uow: UnitOfWork) -> None:
    events = []
    for usage in target.usages:
        if usage.need_to_renew:
            dt = get_current_datetime()
            delta = 0 - usage.used_units
            usage.renew()

            subscription_updated = SubscriptionUpdated(
                subscription_id=target.id,
                changed_fields=(f"usages.{usage.code}:updated",),
                auth_id=target.auth_id,
                occurred_at=dt,
            )

            subscription_usage_updated = SubscriptionUsageUpdated(
                subscription_id=target.id,
                title=usage.title,
                code=usage.code,
                unit=usage.unit,
                available_units=usage.available_units,
                used_units=usage.used_units,
                delta=delta,
                auth_id=target.auth_id,
                occurred_at=dt,
            )
            events.append(subscription_updated)
            events.append(subscription_usage_updated)
    if events:
        await uow.subscription_repo().update_one(target)
        for ev in events:
            uow.push_event(ev)
