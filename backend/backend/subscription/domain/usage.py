from datetime import timedelta
from typing import Self

from pydantic import AwareDatetime

from backend.shared.event_driven.eventable import Eventable
from backend.shared.utils.dt import get_current_datetime
from backend.subscription.domain.cycle import Period


class UsageRate(Eventable):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period

    def __init__(self, title: str, code: str, unit: str, available_units: float, renew_cycle: Period):
        super().__init__(title=title, code=code, unit=unit, available_units=available_units, renew_cycle=renew_cycle)

    def __eq__(self, other):
        if not isinstance(other, UsageRate):
            return False
        return all([
            self.title == other.title,
            self.code == other.code,
            self.unit == other.unit,
            self.available_units == other.available_units,
            self.renew_cycle == other.renew_cycle,
        ])


class Usage(Eventable):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
    used_units: float
    last_renew: AwareDatetime

    def __init__(self, title: str, code: str, unit: str, available_units: float, renew_cycle: Period,
                 used_units: float = 0, last_renew: AwareDatetime = None):
        last_renew = last_renew if last_renew else get_current_datetime()
        super().__init__(title=title, code=code, unit=unit, available_units=available_units, used_units=used_units,
                         last_renew=last_renew, renew_cycle=renew_cycle)

    def __eq__(self, other):
        if not isinstance(other, Usage):
            return False
        return all([
            self.title == other.title,
            self.code == other.code,
            self.unit == other.unit,
            self.available_units == other.available_units,
            self.renew_cycle == other.renew_cycle,
            self.used_units == other.used_units,
            self.last_renew == other.last_renew,
        ])

    @classmethod
    def from_usage_rate(cls, usage_rate: UsageRate) -> Self:
        return cls(title=usage_rate.title, code=usage_rate.code, unit=usage_rate.unit,
                   available_units=usage_rate.available_units, renew_cycle=usage_rate.renew_cycle, used_units=0,
                   last_renew=get_current_datetime())

    @property
    def next_renew(self) -> AwareDatetime:
        return self.last_renew + timedelta(self.renew_cycle.get_cycle_in_days())

    @property
    def need_to_renew(self) -> bool:
        return get_current_datetime() > self.renew_cycle.get_next_billing_date(self.last_renew)

    def increase(self, delta: float) -> None:
        self.used_units += delta

    def renew(self):
        self.used_units = 0
        self.last_renew = get_current_datetime()
