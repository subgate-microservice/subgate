import aiohttp

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.shared.event_driven.bus import Context
from backend.webhook.application.telegraph import DeliveryTask
from backend.webhook.domain.delivery_task import Message
from backend.webhook.domain.webhook_repo import WebhookSby

container = get_container()


async def request(method: str, url: str, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()


async def handle_event(event: Event, context: Context):
    # Получаем webhooks, которые нужно отправить
    webhook_repo = context.uow.webhook_repo()
    sby = WebhookSby(
        auth_ids={event.auth_id},
        event_codes={event.get_event_code()},
    )
    webhooks = await webhook_repo.get_selected(sby)

    # Создаем TelegraphMessage для каждого Webhook
    if webhooks:
        data = Message.from_event(event)
        partkey = str(event.id) if hasattr(event, "id") else str(event.subscription_id)
        deliveries = [
            DeliveryTask(
                url=hook.target_url,
                data=data,
                partkey=partkey,
                retries=0,
                delays=hook.delays,
            ) for hook in webhooks
        ]
        await context.uow.delivery_task_repo().add_many(deliveries)
