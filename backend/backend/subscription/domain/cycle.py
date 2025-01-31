import datetime
from enum import StrEnum

from pydantic import AwareDatetime, Field

from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime


class CycleCode(StrEnum):
    Daily = "Daily"
    Weekly = "Weekly"
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    Semiannual = "Semiannual"
    Annual = "Annual"


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
        if code == CycleCode.Monthly:
            return cls(title=CycleCode.Monthly, code=CycleCode.Monthly, cycle_in_days=31)
        raise NotImplemented


def get_next_billing_date(start_date: AwareDatetime, cycle: CycleCode) -> AwareDatetime:
    if cycle == CycleCode.Daily:
        return start_date + datetime.timedelta(days=1)
    if cycle == CycleCode.Weekly:
        return start_date + datetime.timedelta(days=7)
    if cycle == CycleCode.Monthly:
        return start_date + datetime.timedelta(days=31)
    if cycle == CycleCode.Quarterly:
        return start_date + datetime.timedelta(days=92)
    if cycle == CycleCode.Semiannual:
        return start_date + datetime.timedelta(days=183)
    if cycle == CycleCode.Annual:
        return start_date + datetime.timedelta(days=365)
