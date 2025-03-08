import asyncio
from abc import ABC, abstractmethod

from fastapi_users.exceptions import UserNotExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from loguru import logger

from backend import config
from backend.auth.application.apikey_service import ApikeyCreate, ApikeyManager
from backend.auth.infra.fastapi_users.database import User
from backend.auth.infra.fastapi_users.manager import UserManager
from backend.auth.infra.fastapi_users.schemas import UserCreate
from backend.bootstrap import get_container
from backend.events import EVENTS
from backend.shared.database import drop_and_create_postgres_tables
from backend.subscription.application.subscription_manager import SubManager
from backend.webhook.adapters import subscription_handlers

container = get_container()


class Startup(ABC):
    @abstractmethod
    async def run(self):
        pass


class DatabaseStartup(Startup):
    async def run(self):
        await drop_and_create_postgres_tables()


class FirstUserStartup(Startup):
    def __init__(self):
        self._email = config.USER_EMAIL
        self._pass = config.USER_PASSWORD
        self._apikey_title = config.USER_APIKEY_TITLE
        self._apikey_public_id = config.USER_APIKEY_PUBLIC_ID
        self._apikey_secret = config.USER_APIKEY_SECRET
        self._auth_user = None

    async def _create_auth_user_if_not_exist(self):
        session_factory = container.session_factory()
        async with session_factory() as session:
            user_db = SQLAlchemyUserDatabase(session, User)
            manager = UserManager(user_db)
            try:
                result = await manager.get_by_email(self._email)
                logger.info("AuthUser already exist")
            except UserNotExists:
                logger.info("Creating AuthUser")
                user_create = UserCreate(email=self._email, password=self._pass)
                result = await manager.create(user_create)
            await session.commit()
        self._auth_user = result.to_auth_user()

    async def _create_apikey_if_not_exist(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            apikey_manager = ApikeyManager(uow)
            apikey = ApikeyCreate(
                title=self._apikey_title,
                auth_user=self._auth_user,
                public_id=self._apikey_public_id,
                secret=self._apikey_secret,
            )
            try:
                _ = await apikey_manager.get_by_public_id(self._apikey_public_id)
                logger.info("Apikey already created")
            except LookupError:
                logger.info("Crating apikey")
                await apikey_manager.create(apikey)

            await uow.commit()

    async def run(self):
        await self._create_auth_user_if_not_exist()
        await self._create_apikey_if_not_exist()


class EventbusStartup(Startup):
    async def run(self):
        logger.info("Subscribe events to eventbus")
        bus = get_container().eventbus()
        for event_type in EVENTS:
            bus.subscribe(event_type, subscription_handlers.handle_subscription_domain_event)


class WorkersStartup(Startup):
    @staticmethod
    def _telegraph_worker():
        logger.info("Run telegraph worker")
        telegraph = container.telegraph()
        task = asyncio.create_task(telegraph.run_worker())
        task.set_name("TelegraphWorker")

    @staticmethod
    def _submanage_worker():
        logger.info("Run subscription manage worker")
        manager = SubManager(
            container.unit_of_work_factory(),
            config.SUBSCRIPTION_MANAGER_BULK_LIMIT,
            config.SUBSCRIPTION_MANAGER_CHECK_PERIOD,
        )
        task = asyncio.create_task(manager.run_worker())
        task.set_name("SubscriptionManagerWorker")

    async def run(self):
        logger.info("Run startup workers")
        self._telegraph_worker()
        self._submanage_worker()


async def run_preparations():
    await DatabaseStartup().run()
    await FirstUserStartup().run()
    await EventbusStartup().run()
    await WorkersStartup().run()
