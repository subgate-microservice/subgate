from typing import NamedTuple

from pydantic import AwareDatetime

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
