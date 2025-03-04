import pytest
from loguru import logger

from backend.bootstrap import get_container
from backend.subscription.domain.events import PlanCreated, PlanUpdated
from backend.webhook.adapters.schemas import WebhookCreate, WebhookUpdate
from backend.webhook.domain.webhook_repo import WebhookSby
from tests.conftest import client, get_async_client
from tests.fakes import simple_webhook, many_webhooks

container = get_container()


async def event_handler(event, _context):
    logger.debug(event)


container.eventbus().subscribe(PlanCreated, event_handler)
container.eventbus().subscribe(PlanUpdated, event_handler)


class TestCreate:
    @pytest.mark.asycnio
    async def test_create_webhook(self, client):
        payload = WebhookCreate(event_code="plan_created", target_url="http://my-site.com").model_dump(mode="json")
        response = await client.post(f"/webhook/", json=payload)
        response.raise_for_status()


class TestGet:
    @pytest.mark.asyncio
    async def test_get_one_by_id(self, simple_webhook, client):
        response = await client.get(f"/webhook/{simple_webhook.id}")
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_get_all(self, many_webhooks, client):
        response = await client.get(f"/webhook/")
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_get_selected(self, many_webhooks, client):
        params = {"ids": [x.id for x in many_webhooks[0:4]]}
        response = await client.get(f"/webhook/", params=params)
        response.raise_for_status()
        assert len(response.json()) == 4


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update_one(self, simple_webhook, client):
        simple_webhook = simple_webhook.model_copy(update={"target_url": "http://updated-site.com"})
        payload = WebhookUpdate.from_webhook(simple_webhook).model_dump(mode="json")
        response = await client.put(f"/webhook/{simple_webhook.id}", json=payload)
        response.raise_for_status()


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_one_by_id(self, simple_webhook, client):
        response = await client.delete(f"/webhook/{simple_webhook.id}")
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_delete_all_webhooks(self, many_webhooks, client):
        response = await client.delete(f"/webhook/")
        response.raise_for_status()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.webhook_repo().get_selected(WebhookSby())
            assert len(real) == 0

    @pytest.mark.asyncio
    async def test_delete_selected_webhooks(self, many_webhooks, client):
        params = {"ids": [many_webhooks[0].id, many_webhooks[1].id]}
        response = await client.delete(f"/webhook/", params=params)
        response.raise_for_status()

        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.webhook_repo().get_selected(WebhookSby())
            assert len(real) == len(many_webhooks) - len(params["ids"])
