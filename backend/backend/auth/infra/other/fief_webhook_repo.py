from uuid import UUID

from backend.auth.infra.other.fief_base_repo import FiefBaseRepo
from backend.auth.infra.other.fief_schemas import FiefWebhook, FiefWebhookCreate

WEBHOOK_SECRETS: dict[str, str] = {}


class FiefWebhookRepo(FiefBaseRepo):

    async def get_all(self) -> list[FiefWebhook]:
        response = await self._request("GET", f"/webhooks")
        result = [FiefWebhook.from_fief_dict(x) for x in response["results"]]
        return result

    async def delete_all(self) -> None:
        webhooks = await self.get_all()
        for hook in webhooks:
            await self.delete_by_id(hook.id)

    async def delete_by_id(self, webhook_id: UUID) -> None:
        await self._request("DELETE", f"/webhooks/{webhook_id}")

    async def create_one(self, data: FiefWebhookCreate) -> FiefWebhook:
        data = await self._request("POST", "/webhooks", json=data.model_dump(mode="json"))
        secret = data.pop("secret")
        result = FiefWebhook.from_fief_dict(data)
        WEBHOOK_SECRETS[result.event] = secret
        return result

    @staticmethod
    def get_webhook_secret(event_code: str) -> str:
        return WEBHOOK_SECRETS[event_code]
