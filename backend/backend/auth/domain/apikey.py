import secrets
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthUser
from backend.shared.base_models import MyBase
from backend.shared.utils import get_current_datetime

ApikeyId = UUID


class Apikey(MyBase):
    id: ApikeyId = Field(default_factory=uuid4)
    title: str
    auth_user: AuthUser
    value: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)

    def to_light_bson(self):
        result = self.model_dump(exclude={"value", "auth_user"}, mode="json")
        return result
