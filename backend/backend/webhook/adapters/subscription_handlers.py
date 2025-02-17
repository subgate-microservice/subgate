import json

import aiohttp

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.webhook.application.telegraph import Telegram
from backend.webhook.domain.webhook_repo import WebhookSby

container = get_container()


async def request(method: str, url: str, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()


async def handle_subscription_event(event: Event, _context):
    # Превращаем Event в закодированную строку
    auth_user_id = event.payload.auth_id
    data_for_send = {
        "type": "event",
        "code": event.code,
        "payload": event.payload.model_dump(mode="json"),
    }
    data_strig = json.dumps(data_for_send)
    encrypted_data = container.encrypt_service().encrypt(data_strig)

    # Получаем webhooks, которые нужно отправить
    webhook_repo = event.context.uow.webhook_repo()
    sby = WebhookSby(
        auth_ids={auth_user_id},
        event_codes={event.code},
    )
    webhooks = await webhook_repo.get_selected(sby)

    # Создаем TelegraphMessage из каждого Webhook и ставим сообщение в очередь
    telegraph = container.telegraph()
    for hook in webhooks:
        message = Telegram(url=hook.target_url, data=encrypted_data)
        await telegraph.save_message(message)
