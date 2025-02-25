from typing import Union, Self
from uuid import UUID

from pydantic import Field, AwareDatetime, model_validator

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase

WebhookId = UUID


class Webhook(MyBase):
    id: WebhookId
    event_code: str
    target_url: str
    max_retries: int
    delays: Union[tuple[int, ...], int]
    auth_id: AuthId = Field(exclude=True)
    created_at: AwareDatetime
    updated_at: AwareDatetime
