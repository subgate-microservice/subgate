from typing import Iterable

from loguru import logger

from backend.auth.infra.other.fief.fief_client_repo import FiefClientRepo
from backend.auth.infra.other.fief.fief_schemas import FiefWebhookCreate, FiefClientPartialUpdate
from backend.auth.infra.other.fief.fief_webhook_repo import FiefWebhookRepo


class FiefWebhookPreparation:
    def __init__(
            self,
            expected_events: Iterable[str],
            webhook_base_url: str,
            webhook_repo: FiefWebhookRepo,
    ):
        self._expected_events = expected_events
        self._webhook_base_url = webhook_base_url
        self._webhook_repo = webhook_repo

    async def _create_webhooks(self):
        await self._webhook_repo.delete_all()
        webhooks_for_create = [
            FiefWebhookCreate(
                url=f"{self._webhook_base_url}/{event.replace('.', '-')}",
                events=[event]
            ) for event in self._expected_events
        ]
        if len(webhooks_for_create):
            for hook in webhooks_for_create:
                await self._webhook_repo.create_one(hook)
        logger.info(f"Webhooks were created: {webhooks_for_create}")

    async def execute(self):
        await self._create_webhooks()


class FiefClientPreparation:
    def __init__(
            self,
            redirects: Iterable[str],
            client_repo: FiefClientRepo,
    ):
        self._redirects = redirects
        self._client_repo = client_repo

    async def execute(self):
        clients = await self._client_repo.get_all()
        client = clients[0]
        new_redirects = set(client.redirect_uris).union(set(self._redirects))
        data = FiefClientPartialUpdate(id=client.id, redirect_uris=new_redirects, client_type="public")
        await self._client_repo.partial_update_one(data)
        logger.info(f"Redirects were updated. Current value is {new_redirects}")
