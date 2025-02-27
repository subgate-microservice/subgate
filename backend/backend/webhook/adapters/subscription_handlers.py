import aiohttp

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.shared.event_driven.bus import Context
from backend.webhook.application.telegraph import DeliveryTask
from backend.webhook.domain.delivery_task import Message
from backend.webhook.domain.webhook_repo import WebhookSby

container = get_container()

EVENT_PARTKEY_MAPPING = {
    "sub_created": "id",
    "sub_deleted": "id",
    "sub_updated": "id",
    "plan_created": "id",
    "plan_deleted": "id",
    "plan_updated": "id",
    "sub_usage_added": "subscription_id",
    "sub_usage_removed": "subscription_id",
    "sub_usage_updated": "subscription_id",
    "sub_discount_added": "subscription_id",
    "sub_discount_removed": "subscription_id",
    "sub_discount_updated": "subscription_id",
    "sub_paused": "id",
    "sub_resumed": "id",
    "sub_expired": "id",
    "sub_renewed": "id",
}


async def request(method: str, url: str, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()


async def handle_subscription_domain_event(event: Event, context: Context):
    event_code = event.get_event_code()
    sby = WebhookSby(auth_ids={event.auth_id}, event_codes={event_code})
    webhooks = await context.uow.webhook_repo().get_selected(sby)

    if webhooks:
        partkey_attr = EVENT_PARTKEY_MAPPING[event.get_event_code()]
        partkey = str(getattr(event, partkey_attr))
        message = Message.from_event(event)
        deliveries = [
            DeliveryTask(
                url=hook.target_url,
                data=message,
                partkey=partkey,
                retries=0,
                delays=hook.delays,
            ) for hook in webhooks
        ]
        await context.uow.delivery_task_repo().add_many(deliveries)
