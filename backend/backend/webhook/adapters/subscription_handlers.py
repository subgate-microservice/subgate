import json

import aiohttp
from loguru import logger

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.shared.event_driven.bus import Context
from backend.webhook.application.telegraph import Telegram
from backend.webhook.domain.webhook_repo import WebhookSby

container = get_container()


async def request(method: str, url: str, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()


async def handle_subscription_event(event: Event, context: Context):
    auth_user_id = event.auth_id
    data_for_send = {
        "type": "event",
        "code": event.get_event_code(),
        "payload": event.model_dump(mode="json"),
    }

    # Получаем webhooks, которые нужно отправить
    webhook_repo = context.uow.webhook_repo()
    sby = WebhookSby(
        auth_ids={auth_user_id},
        event_codes={event.get_event_code()},
    )
    webhooks = await webhook_repo.get_selected(sby)

    # Создаем TelegraphMessage для каждого Webhook
    telegrams = [Telegram(url=hook.target_url, data=data_for_send) for hook in webhooks]
    await context.uow.telegram_repo().add_many(telegrams)
