from typing import Literal

from pydantic import AwareDatetime

Lock = Literal["read", "write", "none"]
UnionValue = [int, float, bool, str, AwareDatetime]
