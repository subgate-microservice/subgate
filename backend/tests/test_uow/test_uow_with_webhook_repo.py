import pytest

from backend.bootstrap import get_container
from backend.webhook.domain.webhook_repo import WebhookSby
from tests.fake_data import create_webhook

container = get_container()


@pytest.mark.asyncio
async def test_create_one():
    async with container.unit_of_work_factory().create_uow() as uow:
        item = create_webhook()

        await uow.webhook_repo().add_one(item)
        with pytest.raises(LookupError):
            await uow.webhook_repo().get_one_by_id(item.id)

        await uow.commit()
        await uow.webhook_repo().get_one_by_id(item.id)

        await uow.rollback()
        with pytest.raises(LookupError):
            await uow.webhook_repo().get_one_by_id(item.id)


@pytest.mark.asyncio
async def test_create_many():
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [create_webhook() for _ in range(11)]

        await uow.webhook_repo().add_many(items)
        real = await uow.webhook_repo().get_selected(WebhookSby())
        assert len(real) == 0

        await uow.commit()
        real = await uow.webhook_repo().get_selected(WebhookSby())
        assert len(real) == len(items)

        await uow.rollback()
        real = await uow.webhook_repo().get_selected(WebhookSby())
        assert len(real) == 0


@pytest.mark.asyncio
async def test_update_one():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        old_item = create_webhook()
        await uow.webhook_repo().add_one(old_item)
        await uow.commit()

    # Test
    async with container.unit_of_work_factory().create_uow() as uow:
        # Update
        updated_item = old_item.model_copy(deep=True, update={"target_url": "https://new-url.com"})
        await uow.webhook_repo().update_one(updated_item)

        # Without commit
        real = await uow.webhook_repo().get_one_by_id(old_item.id)
        assert real == old_item

        # With commit
        await uow.commit()
        real = await uow.webhook_repo().get_one_by_id(old_item.id)
        assert real == updated_item

        # With rollback
        await uow.rollback()
        real = await uow.webhook_repo().get_one_by_id(old_item.id)
        assert real == old_item


@pytest.mark.asyncio
async def test_delete_one():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        item = create_webhook()
        await uow.webhook_repo().add_one(item)
        await uow.commit()

    # Test without commit
    async with container.unit_of_work_factory().create_uow() as uow:
        target = await uow.webhook_repo().get_one_by_id(item.id)
        await uow.webhook_repo().delete_one(target)
        real = await uow.webhook_repo().get_one_by_id(item.id)
        assert real.id == item.id

        # Test with commit
        await uow.commit()
        with pytest.raises(LookupError):
            _ = await uow.webhook_repo().get_one_by_id(item.id)

        # Test with rollback
        await uow.rollback()
        real = await uow.webhook_repo().get_one_by_id(item.id)
        assert real.id == item.id


@pytest.mark.asyncio
async def test_delete_many():
    # Before
    async with container.unit_of_work_factory().create_uow() as uow:
        items = [create_webhook() for _ in range(11)]
        await uow.webhook_repo().add_many(items)
        await uow.commit()

    # Test without commit
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.webhook_repo().delete_many(items)
        real = await uow.webhook_repo().get_selected(WebhookSby())
        assert len(real) == len(items)

        # Test with commit
        await uow.commit()
        real = await uow.webhook_repo().get_selected(WebhookSby())
        assert len(real) == 0

        # Test with rollback
        await uow.rollback()
        real = await uow.webhook_repo().get_selected(WebhookSby())
        assert len(real) == len(items)
