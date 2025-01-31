import asyncio

from loguru import logger

from backend import config
from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.other.fief_client_repo import FiefClientRepo
from backend.auth.infra.other.fief_startup_services import FiefWebhookPreparation, FiefClientPreparation
from backend.auth.infra.other.fief_webhook_repo import FiefWebhookRepo
from backend.bootstrap import get_container
from backend.shared.events import EventCode
from backend.webhook.adapters import subscription_handlers

container = get_container()


async def _fief_webhook_preparation():
    expected_events = config.FIEF_EVENTS
    webhook_base_url = config.FIEF_WEBHOOK_BASE_URL
    webhook_repo = FiefWebhookRepo(
        config.FIEF_BASE_URL,
        config.FIEF_ADMIN_APIKEY,
    )
    await FiefWebhookPreparation(expected_events, webhook_base_url, webhook_repo).execute()


async def _fief_client_preparation():
    redirects = config.FIEF_REDIRECT_URLS
    client_repo = FiefClientRepo(config.FIEF_BASE_URL, config.FIEF_ADMIN_APIKEY)
    await FiefClientPreparation(redirects, client_repo).execute()


async def _run_fief_preparations():
    auth_closure_factory = container.auth_closure_factory()
    code = auth_closure_factory.get_code()
    if code == "fief_factory" or code == "complex_factory_with_fief":
        logger.info("Fief preparations...")
        await asyncio.sleep(10)
        await _fief_client_preparation()
        await _fief_webhook_preparation()


async def _create_apikey_if_not_exist():
    apikey = Apikey(
        title="HelloApi",
        auth_user=AuthUser(),
        value="BCxKH--Vls-LiXLOJ-FH-DJgjGqm7ioCrZK8Uc_1eFg",
    )
    try:
        async with get_container().unit_of_work_factory().create_uow() as uow:
            await uow.apikey_repo().get_apikey_by_value(apikey.value)
    except LookupError:
        logger.info("Creating apikey...")
        async with get_container().unit_of_work_factory().create_uow() as uow:
            await uow.apikey_repo().add_one(apikey)
            await uow.commit()


async def _subscribe_events_to_eventbus():
    logger.info("Subscribe events to eventbus")
    bus = get_container().eventbus()
    for event_code in EventCode:
        bus.subscribe(event_code, subscription_handlers.handle_subscription_event)


async def _create_indexes():
    logger.info("Create indexes in database")
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().create_indexes()
        await uow.plan_repo().create_indexes()
        await uow.webhook_repo().create_indexes()
        await uow.commit()


async def run_preparations():
    logger.info("Run application preparations...")
    await _run_fief_preparations()
    await _create_apikey_if_not_exist()
    await _subscribe_events_to_eventbus()
    # await _create_indexes()
