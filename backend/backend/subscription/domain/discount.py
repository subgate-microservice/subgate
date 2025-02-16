import dataclasses
from typing import NamedTuple, Optional

from pydantic import AwareDatetime


@dataclasses.dataclass
class Discount:
    title: str
    code: str
    description: Optional[str]
    size: float
    valid_until: Optional[AwareDatetime]
