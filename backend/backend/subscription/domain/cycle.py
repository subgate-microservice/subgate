import datetime
from enum import StrEnum

from pydantic import AwareDatetime

from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime

_cycle_days = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 92,
    "semiannual": 183,
    "annual": 365,
    "lifetime": 365_000,
}


class Period(StrEnum):
    Daily = "daily"
    Weekly = "weekly"
    Monthly = "monthly"
    Quarterly = "quarterly"
    Semiannual = "semiannual"
    Annual = "annual"
    Lifetime = "lifetime"

    def get_cycle_in_days(self) -> int:
        return _cycle_days[self.value]

    def get_next_billing_date(self, from_date: AwareDatetime = None) -> AwareDatetime:
        if from_date is None:
            from_date = get_current_datetime()
        return from_date + datetime.timedelta(self.get_cycle_in_days())


class Cycle(MyBase):
    title: str
    code: Period
    cycle_in_days: int

    def get_next_billing_date(self, from_date: AwareDatetime = None) -> AwareDatetime:
        if from_date is None:
            from_date = get_current_datetime()
        return from_date + datetime.timedelta(self.cycle_in_days)

    @classmethod
    def from_code(cls, code: Period):
        if code == Period.Daily:
            return cls(title="Daily", code=Period.Daily, cycle_in_days=1)
        elif code == Period.Weekly:
            return cls(title="Weekly", code=Period.Weekly, cycle_in_days=7)
        elif code == Period.Monthly:
            return cls(title="Monthly", code=Period.Monthly, cycle_in_days=30)
        elif code == Period.Quarterly:
            return cls(title="Quarterly", code=Period.Quarterly, cycle_in_days=30)
        elif code == Period.Semiannual:
            return cls(title="Semiannual", code=Period.Semiannual, cycle_in_days=183)
        elif code == Period.Annual:
            return cls(title="Annual", code=Period.Annual, cycle_in_days=365)
        elif code == Period.Lifetime:
            return cls(title="Lifetime", code=Period.Lifetime, cycle_in_days=365_000)
        raise TypeError(code)
