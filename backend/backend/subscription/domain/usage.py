import dataclasses
from datetime import timedelta
from typing import Self

from pydantic import AwareDatetime

from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period


@dataclasses.dataclass
class UsageRate:
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period


@dataclasses.dataclass
class Usage:
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

    @property
    def next_renew(self) -> AwareDatetime:
        return self.last_renew + timedelta(self.renew_cycle.get_cycle_in_days())

    def increase(self, delta: float) -> None:
        self.used_units += delta
