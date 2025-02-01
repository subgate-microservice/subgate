from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, AwareDatetime, Field

from backend.auth.domain.auth_user import AuthId


class FiefTenant(BaseModel):
    created_at: AwareDatetime
    updated_at: AwareDatetime
    id: UUID
    name: str
    default: bool
    slug: str
    registration_allowed: bool
    theme_id: Optional[str] = None
    logo_url: Optional[str] = None
    application_url: Optional[str] = None
    encrypt_jwk: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class FiefClient(BaseModel):
    created_at: AwareDatetime
    updated_at: AwareDatetime
    id: UUID
    name: str
    first_party: bool
    client_type: str
    client_id: str
    client_secret: str
    redirect_uris: list[str]
    access_id_token_lifetime_seconds: int
    refresh_token_lifetime_seconds: int
    tenant_id: UUID
    tenant: FiefTenant

    model_config = ConfigDict(frozen=True)


class FiefClientPartialUpdate(BaseModel):
    id: UUID
    name: Optional[str] = None
    first_party: Optional[bool] = None
    client_type: Optional[Literal["confidential", "public"]] = None
    redirect_uris: Optional[list[str]] = None
    authorization_code_lifetime_seconds: Optional[int] = None
    access_id_token_lifetime_seconds: Optional[int] = None
    refresh_token_lifetime_seconds: Optional[int] = None


class FiefUserFieldConfiguration(BaseModel):
    at_registration: bool = True
    required: bool = True
    at_update: bool = True
    choices: Optional[list] = None
    default: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class FiefUserField(BaseModel):
    created_at: AwareDatetime
    updated_at: AwareDatetime
    id: UUID
    name: str
    type: str
    configuration: FiefUserFieldConfiguration

    model_config = ConfigDict(frozen=True)


class FiefUserFieldCreate(BaseModel):
    name: str
    slug: str
    type: str = "STRING"
    configuration: FiefUserFieldConfiguration

    model_config = ConfigDict(frozen=True)


class FiefWebhook(BaseModel):
    id: UUID
    url: str
    event: str
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_fief_dict(cls, data: dict) -> "FiefWebhook":
        events = data.pop("events")
        if len(events) != 1:
            raise ValueError
        return cls(**data, event=events.pop())


class FiefWebhookCreate(BaseModel):
    url: str
    events: list[str]

    model_config = ConfigDict(frozen=True)


class FiefUser(BaseModel):
    id: UUID
    email: str
    is_active: bool
    email_verified: bool
    tenant_id: UUID
    fields: dict
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(frozen=True)


class FiefUserCreate(BaseModel):
    email: str
    email_verified: bool
    is_active: bool
    tenant_id: UUID
    password: str
    fields: dict = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


class FiefUserCreated(BaseModel):
    id: AuthId
    email: str
    email_verified: bool
    is_active: bool
    fields: dict[str, str]
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(frozen=True)
