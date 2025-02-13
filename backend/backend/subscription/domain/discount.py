from typing import NamedTuple, Optional

from pydantic import AwareDatetime


class Discount(NamedTuple):
    title: str
    code: str
    description: Optional[str]
    size: float
    valid_until: Optional[AwareDatetime]
