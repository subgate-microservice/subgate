from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake


class MyBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_snake,
        populate_by_name=True,
        from_attributes=True,
        frozen=True,
    )


class BaseSby(BaseModel):
    skip: int = 0
    limit: int = 100
    order_by: list[tuple[str, int]] = Field(default_factory=lambda: [("created_at", 1)])
