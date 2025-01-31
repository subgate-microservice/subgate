from pydantic import BaseModel


class AccessToken(BaseModel):
    type: str
    token: str
