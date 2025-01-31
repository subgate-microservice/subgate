from backend.shared.unit_of_work.uow import UnitOfWork
from backend.webhook.domain.webhook import Webhook, WebhookId
from backend.webhook.domain.webhook_repo import WebhookSby


class WebhookUsecase:
    def __init__(
            self,
            uow: UnitOfWork,
    ):
        self.uow = uow


class CreateWebhook(WebhookUsecase):
    async def execute(self, webhook: Webhook):
        await self.uow.webhook_repo().add_one(webhook)


class GetSelectedWebhooks(WebhookUsecase):
    async def execute(self, sby: WebhookSby) -> list[Webhook]:
        return await self.uow.webhook_repo().get_selected(sby)


class GetWebhookById(WebhookUsecase):
    async def execute(self, webhook_id: WebhookId) -> Webhook:
        result = await self.uow.webhook_repo().get_one_by_id(webhook_id)
        return result


class UpdateWebhook(WebhookUsecase):
    async def execute(self, webhook: Webhook):
        await self.uow.webhook_repo().update_one(webhook)


class DeleteWebhookById(WebhookUsecase):
    async def execute(self, webhook_id: WebhookId):
        target = await self.uow.webhook_repo().get_one_by_id(webhook_id)
        await self.uow.webhook_repo().delete_one(target)


class DeleteSelectedWebhooks(WebhookUsecase):
    async def execute(self, sby: WebhookSby):
        targets = await self.uow.webhook_repo().get_selected(sby)
        await self.uow.webhook_repo().delete_many(targets)
