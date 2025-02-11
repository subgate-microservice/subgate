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


class CycleCode(StrEnum):
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
    code: CycleCode
    cycle_in_days: int

    def get_next_billing_date(self, from_date: AwareDatetime = None) -> AwareDatetime:
        if from_date is None:
            from_date = get_current_datetime()
        return from_date + datetime.timedelta(self.cycle_in_days)

    @classmethod
    def from_code(cls, code: CycleCode):
        if code == CycleCode.Daily:
            return cls(title="Daily", code=CycleCode.Daily, cycle_in_days=1)
        elif code == CycleCode.Weekly:
            return cls(title="Weekly", code=CycleCode.Weekly, cycle_in_days=7)
        elif code == CycleCode.Monthly:
            return cls(title="Monthly", code=CycleCode.Monthly, cycle_in_days=30)
        elif code == CycleCode.Quarterly:
            return cls(title="Quarterly", code=CycleCode.Quarterly, cycle_in_days=30)
        elif code == CycleCode.Semiannual:
            return cls(title="Semiannual", code=CycleCode.Semiannual, cycle_in_days=183)
        elif code == CycleCode.Annual:
            return cls(title="Annual", code=CycleCode.Annual, cycle_in_days=365)
        elif code == CycleCode.Lifetime:
            return cls(title="Lifetime", code=CycleCode.Lifetime, cycle_in_days=365_000)
        raise TypeError(code)
