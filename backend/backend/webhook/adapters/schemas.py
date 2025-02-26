from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime
from backend.webhook.domain.webhook import WebhookId, Webhook

DELAYS = (0, 9, 29, 180, 600, 1_800, 3_600, 7_200, 14_400, 28_800, 57_600, 86_400)


class WebhookCreate(MyBase):
    id: WebhookId = Field(default_factory=uuid4)
    event_code: str
    target_url: str
    delays: tuple[int, ...] = DELAYS

    def to_webhook(self, auth_id: AuthId):
        dt = get_current_datetime()
        return Webhook(
            id=self.id,
            event_code=self.event_code,
            target_url=self.target_url,
            delays=self.delays,
            auth_id=auth_id,
            created_at=dt,
            updated_at=dt,
        )


class WebhookUpdate(MyBase):
    id: WebhookId
    event_code: str
    target_url: str
    delays: tuple[int, ...]

    def to_webhook(self, auth_id: AuthId, created_at: AwareDatetime):
        return Webhook(
            id=self.id,
            auth_id=auth_id,
            delays=self.delays,
            event_code=self.event_code,
            target_url=self.target_url,
            created_at=created_at,
            updated_at=get_current_datetime(),
        )

    @classmethod
    def from_webhook(cls, hook: Webhook):
        return cls(id=hook.id, event_code=hook.event_code, target_url=hook.target_url, delays=hook.delays)
