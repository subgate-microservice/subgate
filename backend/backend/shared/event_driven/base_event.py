from pydantic import BaseModel, ConfigDict


class Event(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    @property
    def event_code(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.event_code}"
