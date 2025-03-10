from datetime import datetime
from typing import Union, Mapping
from uuid import UUID

from pydantic import AwareDatetime

from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.enums import SubscriptionStatus
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import PlanInfo, BillingInfo, Subscription
from backend.subscription.domain.usage import UsageRate, Usage


def deserialize_datetime(dt: Union[str, AwareDatetime]) -> AwareDatetime:
    if isinstance(dt, AwareDatetime):
        return dt
    dt = str(dt)
    return datetime.fromisoformat(dt)


def deserialize_uuid(uuid: Union[UUID, str]) -> UUID:
    if isinstance(uuid, UUID):
        return uuid
    return UUID(uuid)


def deserialize_usage_rate(data: Mapping) -> UsageRate:
    renew_cycle = Period(data["renew_cycle"])
    return UsageRate(
        title=data["title"],
        code=data["code"],
        unit=data["unit"],
        available_units=data["available_units"],
        renew_cycle=renew_cycle,
    )


def deserialize_usage(data: Mapping) -> Usage:
    renew_cycle = Period(data["renew_cycle"])
    last_renew = deserialize_datetime(data["last_renew"])
    return Usage(
        title=data["title"],
        code=data["code"],
        unit=data["unit"],
        available_units=data["available_units"],
        renew_cycle=renew_cycle,
        last_renew=last_renew,
        used_units=data["used_units"],
    )


def deserialize_discount(data: Mapping) -> Discount:
    valid_until = deserialize_datetime(data["valid_until"])
    return Discount(
        title=data["title"],
        code=data["code"],
        description=data["description"],
        size=data["size"],
        valid_until=valid_until,
    )


def deserialize_plan(data: Mapping) -> Plan:
    plan_id = deserialize_uuid(data["id"])
    billing_cycle = Period(data["billing_cycle"])
    usage_rates = [deserialize_usage_rate(x) for x in data["usage_rates"]]
    discounts = [deserialize_discount(x) for x in data["discounts"]]
    auth_id = deserialize_uuid(data["auth_id"])
    created_at = deserialize_datetime(data["created_at"])
    updated_at = deserialize_datetime(data["updated_at"])
    return Plan(
        id=plan_id,
        title=data["title"],
        price=data["price"],
        currency=data["currency"],
        billing_cycle=billing_cycle,
        description=data["description"],
        level=data["level"],
        features=data["features"],
        usage_rates=usage_rates,
        discounts=discounts,
        fields=data["fields"],
        auth_id=auth_id,
        created_at=created_at,
        updated_at=updated_at,
    )


def deserialize_plan_info(plan_info: Mapping) -> PlanInfo:
    plan_id = deserialize_uuid(plan_info["id"])
    return PlanInfo(
        id=plan_id,
        title=plan_info["title"],
        description=plan_info["description"],
        level=plan_info["level"],
        features=plan_info["features"],
    )


def deserialize_billing_info(billing_info: Mapping) -> BillingInfo:
    last_billing = deserialize_datetime(billing_info["last_billing"], )
    billing_cycle = Period(billing_info["billing_cycle"])
    return BillingInfo(
        price=billing_info["price"],
        currency=billing_info["currency"],
        billing_cycle=billing_cycle,
        last_billing=last_billing,
        saved_days=billing_info["saved_days"],
    )


def deserialize_subscription(sub: Mapping) -> Subscription:
    id_ = deserialize_uuid(sub["id"])
    paused_from = deserialize_datetime(sub["paused_from"])
    created_at = deserialize_datetime(sub["created_at"])
    updated_at = deserialize_datetime(sub["updated_at"])
    usages = [deserialize_usage(x) for x in sub["usages"]]
    discounts = [deserialize_discount(x) for x in sub["discounts"]]
    plan_info = deserialize_plan_info(sub["plan_info"])
    billing_info = deserialize_billing_info(sub["billing_info"])
    auth_id = deserialize_uuid(sub["auth_id"])
    status = SubscriptionStatus(sub["status"])
    return Subscription.create_unsafe(
        id=id_,
        status=status,
        paused_from=paused_from,
        created_at=created_at,
        updated_at=updated_at,
        usages=usages,
        discounts=discounts,
        plan_info=plan_info,
        billing_info=billing_info,
        subscriber_id=sub["subscriber_id"],
        auth_id=auth_id,
        fields=sub["fields"],
    )
