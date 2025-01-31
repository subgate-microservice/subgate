import hmac
import json
import time
from hashlib import sha256

from starlette import status

from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.other.fief_webhook_repo import FiefWebhookRepo
from fastapi import Request, HTTPException


class FiefWebhookConverter:
    def __init__(
            self,
            webhook_client: FiefWebhookRepo,
    ):
        self._webhook_client = webhook_client

    async def request_to_json(self, request: Request, event_code: str):
        timestamp = request.headers.get("X-Fief-Webhook-Timestamp")
        signature = request.headers.get("X-Fief-Webhook-Signature")
        payload = (await request.body()).decode("utf-8")

        # Check if timestamp and signature are there
        if timestamp is None or signature is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Check if timestamp is not older than 5 minutes
        if int(time.time()) - int(timestamp) > 5 * 60:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Compute signature
        message = f"{timestamp}.{payload}"
        my_hash = hmac.new(
            self._webhook_client.get_webhook_secret(event_code).encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha256,
        )
        computed_signature = my_hash.hexdigest()

        # Check if the signatures match
        if not hmac.compare_digest(signature, computed_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Good to go!
        data = json.loads(payload)
        return data

    async def request_to_auth_user(self, request: Request):
        data = await self.request_to_json(request, "user.created")
        data = data["data"]
        # payload = FiefUserCreated(
        #     id=data["id"],
        #     created_at=data["created_at"],
        #     updated_at=data["updated_at"],
        #     email=data["email"],
        #     email_verified=data["email_verified"],
        #     is_active=data["is_active"],
        #     fields=data["fields"],
        # )
        return AuthUser(
            id=data["id"],
        )
