from typing import Union, Optional
from uuid import UUID

from pydantic import AwareDatetime

from backend.subscription.domain.plan import Discount, Plan
from backend.subscription.domain.subscription import Subscription, PlanInfo, BillingInfo
from backend.subscription.domain.usage import UsageRate, Usage


def serialize_datetime(dt: Optional[AwareDatetime], mode="json") -> Union[AwareDatetime, str, None]:
    if dt is None:
        return None
    return dt.isoformat() if mode == "json" else dt


def serialize_uuid(uuid: UUID, mode="json") -> Union[UUID, str]:
    return str(uuid) if mode == "json" else uuid


def serialize_usage_rate(usage_rate: UsageRate, _mode="json") -> dict:
    return {
        "code": usage_rate.code,
        "title": usage_rate.title,
        "unit": usage_rate.unit,
        "available_units": usage_rate.available_units,
        "renew_cycle": usage_rate.renew_cycle,
    }


def serialize_usage(usage: Usage, mode="json") -> dict:
    last_renew = serialize_datetime(usage.last_renew, mode)
    return {
        "code": usage.code,
        "title": usage.title,
        "unit": usage.unit,
        "available_units": usage.available_units,
        "renew_cycle": usage.renew_cycle,
        "used_units": usage.used_units,
        "last_renew": last_renew,
    }


def serialize_discount(discount: Discount, mode="json") -> dict:
    valid_until = serialize_datetime(discount.valid_until, mode)
    return {
        "code": discount.code,
        "title": discount.title,
        "size": discount.size,
        "valid_until": valid_until,
        "description": discount.description,
    }


def serialize_plan(plan: Plan, mode="json") -> dict:
    plan_id = serialize_uuid(plan.id, mode)
    usage_rates = [serialize_usage_rate(x, mode) for x in plan.usage_rates]
    discounts = [serialize_discount(x, mode) for x in plan.discounts]
    auth_id = serialize_uuid(plan.auth_id, mode)
    created_at = serialize_datetime(plan.created_at, mode)
    updated_at = serialize_datetime(plan.updated_at, mode)
    return {
        "id": plan_id,
        "title": plan.title,
        "price": plan.price,
        "currency": plan.currency,
        "billing_cycle": plan.billing_cycle,
        "description": plan.description,
        "level": plan.level,
        "features": plan.features,
        "usage_rates": usage_rates,
        "discounts": discounts,
        "fields": plan.fields,
        "auth_id": auth_id,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def serialize_plan_info(plan_info: PlanInfo, mode="json") -> dict:
    plan_id = serialize_uuid(plan_info.id, mode)
    return {
        "id": plan_id,
        "title": plan_info.title,
        "description": plan_info.description,
        "level": plan_info.level,
        "features": plan_info.features,
    }


def serialize_billing_info(billing_info: BillingInfo, mode="json") -> dict:
    last_billing = serialize_datetime(billing_info.last_billing, mode)
    return {
        "price": billing_info.price,
        "currency": billing_info.currency,
        "billing_cycle": billing_info.billing_cycle,
        "last_billing": last_billing,
        "saved_days": billing_info.saved_days,
    }


def serialize_subscription(sub: Subscription, mode="json") -> dict:
    id_ = serialize_uuid(sub.id, mode)
    paused_from = serialize_datetime(sub.paused_from, mode)
    created_at = serialize_datetime(sub.created_at, mode)
    updated_at = serialize_datetime(sub.updated_at, mode)
    usages = [serialize_usage(x, mode) for x in sub.usages]
    discounts = [serialize_discount(x, mode) for x in sub.discounts]
    plan_info = serialize_plan_info(sub.plan_info, mode)
    billing_info = serialize_billing_info(sub.billing_info, mode)
    auth_id = serialize_uuid(sub.auth_id, mode)
    return {
        "id": id_,
        "status": sub.status,
        "paused_from": paused_from,
        "created_at": created_at,
        "updated_at": updated_at,
        "usages": usages,
        "discounts": discounts,
        "plan_info": plan_info,
        "billing_info": billing_info,
        "subscriber_id": sub.subscriber_id,
        "auth_id": auth_id,
        "fields": sub.fields,
        "autorenew": sub.autorenew,
    }
