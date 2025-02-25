from typing import Union, Self
from uuid import uuid4

from pydantic import Field, AwareDatetime, model_validator

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime
from backend.webhook.domain.webhook import WebhookId, Webhook

DELAYS = (0, 9, 29, 180, 600, 1_800, 3_600, 7_200, 14_400, 28_800, 57_600, 86_400)


class WebhookCreate(MyBase):
    id: WebhookId = Field(default_factory=uuid4)
    event_code: str
    target_url: str
    max_retries: int = 13
    delays: Union[tuple[int, ...], int] = DELAYS

    def to_webhook(self, auth_id: AuthId):
        dt = get_current_datetime()
        return Webhook(
            id=self.id,
            event_code=self.event_code,
            target_url=self.target_url,
            max_retries=self.max_retries,
            delays=self.delays,
            auth_id=auth_id,
            created_at=dt,
            updated_at=dt,
        )

    @model_validator(mode='after')
    def check_delays_len(self) -> Self:
        if isinstance(self.delays, tuple):
            if len(self.delays) != self.max_retries - 1:
                raise ValueError(f"Length of delays must be {self.max_retries - 1}. Real value is {len(self.delays)}")
        return self


class WebhookUpdate(MyBase):
    id: WebhookId
    event_code: str
    target_url: str
    max_retries: int
    delays: tuple[int, ...]

    def to_webhook(self, auth_id: AuthId, created_at: AwareDatetime):
        return Webhook(
            id=self.id,
            auth_id=auth_id,
            max_retries=self.max_retries,
            delays=self.delays,
            event_code=self.event_code,
            target_url=self.target_url,
            created_at=created_at,
            updated_at=get_current_datetime(),
        )

    @model_validator(mode='after')
    def check_delays_len(self) -> Self:
        if isinstance(self.delays, tuple):
            if len(self.delays) != self.max_retries - 1:
                raise ValueError(f"Length of delays must be {self.max_retries - 1}. Real value is {len(self.delays)}")
        return self
