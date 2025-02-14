from datetime import datetime
from typing import Union, Mapping
from uuid import UUID

from pydantic import AwareDatetime

from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.usage import UsageRate


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
