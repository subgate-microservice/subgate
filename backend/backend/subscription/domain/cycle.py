import datetime
from enum import StrEnum

from pydantic import AwareDatetime

from backend.shared.base_models import MyBase
from backend.shared.utils.dt import get_current_datetime

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
