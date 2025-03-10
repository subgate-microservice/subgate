import asyncio
from abc import ABC, abstractmethod
from datetime import timedelta

from fastapi_users.exceptions import UserNotExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from loguru import logger

from backend import config
from backend.auth.application.apikey_service import ApikeyCreate, ApikeyManager
from backend.auth.infra.fastapi_users.manager import UserManager
from backend.auth.infra.fastapi_users.schemas import UserCreate
from backend.auth.infra.fastapi_users.sql_repo import User
from backend.bootstrap import get_container
from backend.events import EVENTS
from backend.shared.database import DatabaseManager
from backend.shared.unit_of_work.change_log import SqlLogRepo
from backend.shared.utils.dt import get_current_datetime
from backend.shared.utils.worker import Worker
from backend.subscription.application.subscription_manager import SubManager
from backend.webhook.adapters import subscription_handlers

container = get_container()


class Startup(ABC):
    @abstractmethod
    async def run(self):
        pass


class DatabaseStartup(Startup):
    async def run(self):
        manager = DatabaseManager(
            host=config.DB_HOST,
            port=config.DB_PORT,
            db_name=config.DB_NAME,
            username=config.DB_USER,
            password=config.DB_PASSWORD,
        )
        await manager.create_database_if_not_exist()
        await manager.create_tables_if_not_exist()


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
    def __init__(self):
        self._subman_worker = Worker(
            SubManager(container.unit_of_work_factory(), config.SUBSCRIPTION_MANAGER_BULK_LIMIT).manage,
            sleep_time=config.SUBSCRIPTION_MANAGER_CHECK_PERIOD,
            safe=False,
            task_name="SubManager worker",
        )

        self._log_cleaner_worker = Worker(
            self._clean_old_logs,
            sleep_time=86_400,
            safe=False,
            task_name="LogCleaner worker",
        )

        self._delivery_cleaner_worker = Worker(
            self._clean_old_delivery_tasks,
            sleep_time=86_400,
            safe=False,
            task_name="DeliveryCleaner worker",
        )

        self._telegraph_worker = container.telegraph_worker()

    @staticmethod
    async def _clean_old_logs():
        session_factory = container.session_factory()
        async with session_factory() as session:
            repo = SqlLogRepo(session)
            dt = get_current_datetime().replace(second=0, microsecond=0) - timedelta(days=config.LOG_RETENTION_DAYS)
            await repo.delete_old_logs(dt)
            await session.commit()
        logger.info(f"Logs before {dt.strftime("%Y-%m-%d %H:%M")} were deleted")

    @staticmethod
    async def _clean_old_delivery_tasks():
        async with container.unit_of_work_factory().create_uow() as uow:
            dt = get_current_datetime().replace(second=0, microsecond=0) - timedelta(days=config.LOG_RETENTION_DAYS)
            await uow.delivery_task_repo().delete_many_before_date(dt)
            await uow.commit()
        logger.info(f"Deliveries before {dt.strftime("%Y-%m-%d %H:%M")} were deleted")

    async def run(self):
        self._subman_worker.run()
        self._telegraph_worker.run()
        self._log_cleaner_worker.run()
        self._delivery_cleaner_worker.run()

    async def stop(self):
        self._subman_worker.stop()
        self._telegraph_worker.stop()
        self._log_cleaner_worker.stop()
        self._delivery_cleaner_worker.stop()


class StartupShutdownManager:
    def __init__(self):
        self._database_startup = DatabaseStartup()
        self._first_user_startup = FirstUserStartup()
        self._workers_startup = WorkersStartup()
        self._eventbus_startup = EventbusStartup()

    async def on_startup(self):
        logger.info("On startup")
        await self._database_startup.run()
        await self._eventbus_startup.run()
        await self._first_user_startup.run()
        await self._workers_startup.run()

    async def on_shutdown(self):
        logger.info("On shutdown")
        await self._workers_startup.stop()
        await asyncio.sleep(1)
