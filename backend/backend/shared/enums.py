from typing import Literal, Union

from pydantic import AwareDatetime

Lock = Literal["read", "write", "none"]
UnionValue = Union[int, float, bool, str, AwareDatetime]
