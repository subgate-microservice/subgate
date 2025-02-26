from typing import Optional

from pydantic import AwareDatetime

from backend.shared.event_driven.eventable import Eventable


class Discount(Eventable):
    title: str
    code: str
    description: Optional[str]
    size: float
    valid_until: AwareDatetime

    def __init__(self, title: str, code: str, description: str, size: float, valid_until: AwareDatetime):
        super().__init__(title=title, code=code, description=description, size=size, valid_until=valid_until)

    def __eq__(self, other):
        if not isinstance(other, Discount):
            return False
        return all([
            self.title == other.title,
            self.code == other.code,
            self.size == other.size,
            self.description == other.description,
            self.valid_until == other.valid_until,
        ])
