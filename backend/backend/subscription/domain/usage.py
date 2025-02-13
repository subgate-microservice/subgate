from typing import NamedTuple

from backend.subscription.domain.cycle import Period


class UsageRate(NamedTuple):
    code: str
    title: str
    unit: str
    available_units: float
    renew_cycle: Period
