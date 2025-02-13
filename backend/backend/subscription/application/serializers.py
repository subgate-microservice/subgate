from typing import Union
from uuid import UUID

from pydantic import AwareDatetime

from backend.subscription.domain.plan import DiscountOld, Plan
from backend.subscription.domain.usage import UsageRate


def serialize_datetime(dt: AwareDatetime, mode="json") -> Union[AwareDatetime, str]:
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


def serialize_discounts(discount: DiscountOld, mode="json") -> dict:
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
    discounts = [serialize_discounts(x, mode) for x in plan.discounts]
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
