import asyncio

from fastapi_users.exceptions import UserNotExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from loguru import logger

from backend import config
from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.fastapi_users.database import User
from backend.auth.infra.fastapi_users.manager import UserManager
from backend.auth.infra.fastapi_users.schemas import UserCreate
from backend.bootstrap import get_container
from backend.events import EVENTS
from backend.shared.database import drop_and_create_postgres_tables
from backend.webhook.adapters import subscription_handlers

container = get_container()


async def _create_auth_user_if_not_exist(email: str, password: str) -> AuthUser:
    session_factory = container.session_factory()
    async with session_factory() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        manager = UserManager(user_db)
        try:
            result = await manager.get_by_email(email)
        except UserNotExists:
            user_create = UserCreate(email=email, password=password)
            result = await manager.create(user_create)
        await session.commit()
    return result


async def _create_apikey_if_not_exist(auth_user: AuthUser, title: str, value: str):
    apikey = Apikey(
        title=title,
        auth_user=auth_user,
        value=value,
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
    for event_type in EVENTS:
        bus.subscribe(event_type, subscription_handlers.handle_subscription_domain_event)


async def _create_database():
    await drop_and_create_postgres_tables()


async def run_preparations():
    logger.info("Run application preparations...")
    await _create_database()
    auth_user = await _create_auth_user_if_not_exist(config.USER_EMAIL, config.USER_PASSWORD)
    await _create_apikey_if_not_exist(auth_user, config.USER_APIKEY_TITLE, config.USER_APIKEY)
    await _subscribe_events_to_eventbus()


def run_workers():
    telegraph = container.telegraph()
    task = asyncio.create_task(telegraph.run_worker())
    task.set_name("TelegraphWorker")
