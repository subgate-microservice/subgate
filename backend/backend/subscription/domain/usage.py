from typing import NamedTuple, Self

from pydantic import AwareDatetime

from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period


class UsageRate(NamedTuple):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period


class Usage(NamedTuple):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
    used_units: float
    last_renew: AwareDatetime

    @classmethod
    def from_usage_rate(cls, usage_rate: UsageRate) -> Self:
        return cls(title=usage_rate.title, code=usage_rate.code, unit=usage_rate.unit,
                   available_units=usage_rate.available_units, renew_cycle=usage_rate.renew_cycle, used_units=0,
                   last_renew=get_current_datetime())
