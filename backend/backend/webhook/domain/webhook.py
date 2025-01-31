from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.events import EventCode
from backend.shared.utils import get_current_datetime

WebhookId = UUID


class Webhook(MyBase):
    id: WebhookId = Field(default_factory=uuid4)
    event_code: EventCode = Field(alias="eventCode")
    target_url: str = Field(alias="targetUrl")
    auth_id: AuthId = Field(alias="authId", exclude=True)
    created_at: AwareDatetime = Field(default_factory=get_current_datetime, alias="createdAt")
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime, alias="updatedAt")
