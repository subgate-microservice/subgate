from typing import NamedTuple

from backend.subscription.domain.cycle import Period


class UsageRate(NamedTuple):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
