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
    def __init__(
            self,
            db_name: str,
            db_host: str,
            db_port: int,
            db_username: str,
            db_pass: str,
            db_recreate=False,
    ):
        self._db_name = db_name
        self._db_host = db_host
        self._db_port = db_port
        self._db_username = db_username
        self._db_pass = db_pass
        self._db_recreate = db_recreate

    async def run(self):
        manager = DatabaseManager(
            host=self._db_host,
            port=self._db_port,
            db_name=self._db_name,
            username=self._db_username,
            password=self._db_pass,
        )
        await manager.create_database_if_not_exist()
        if self._db_recreate:
            await manager.drop_and_create_tables()
        else:
            await manager.create_tables_if_not_exist()


class FirstUserStartup(Startup):
    def __init__(
            self,
            email: str,
            password: str,
            apikey_title: str,
            apikey_public_id: str,
            apikey_secret: str,

    ):
        self._email = email
        self._pass = password
        self._apikey_title = apikey_title
        self._apikey_public_id = apikey_public_id
        self._apikey_secret = apikey_secret
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
                logger.info("Apikey already exist")
            except LookupError:
                logger.info("Creating apikey")
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
    def __init__(
            self,
            subman_bulk_limit: int,
            subman_check_period: int,
            log_retention_days: int,
            delivery_retention_days,
    ):
        self._subman_worker = Worker(
            SubManager(container.unit_of_work_factory(), subman_bulk_limit).manage,
            sleep_time=subman_check_period,
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
        self._log_retention_days = log_retention_days
        self._delivery_retention_days = delivery_retention_days

    async def _clean_old_logs(self):
        session_factory = container.session_factory()
        async with session_factory() as session:
            repo = SqlLogRepo(session)
            dt = get_current_datetime().replace(second=0, microsecond=0) - timedelta(days=self._log_retention_days)
            await repo.delete_old_logs(dt)
            await session.commit()
        logger.info(f"Logs before {dt.strftime("%Y-%m-%d %H:%M")} were deleted")

    async def _clean_old_delivery_tasks(self):
        async with container.unit_of_work_factory().create_uow() as uow:
            dt = get_current_datetime().replace(second=0, microsecond=0) - timedelta(days=self._delivery_retention_days)
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
    def __init__(
            self,
            db_name=config.DB_NAME,
            db_host=config.DB_HOST,
            db_port=config.DB_PORT,
            db_username=config.DB_USER,
            db_pass=config.DB_PASSWORD,
            db_recreate=True,
            user_email=config.USER_EMAIL,
            user_password=config.USER_PASSWORD,
            user_apikey_title=config.USER_APIKEY_TITLE,
            user_apikey_public_id=config.USER_APIKEY_PUBLIC_ID,
            user_apikey_secret=config.USER_APIKEY_SECRET,
            subman_bulk_limit=config.SUBSCRIPTION_MANAGER_BULK_LIMIT,
            subman_check_period=config.SUBSCRIPTION_MANAGER_CHECK_PERIOD,
            log_retention_days=config.LOG_RETENTION_DAYS,
            delivery_retention_days=config.DELIVERY_RETENTION_DAYS,
    ):
        self._database_startup = DatabaseStartup(db_name, db_host, db_port, db_username, db_pass, db_recreate)
        self._first_user_startup = FirstUserStartup(user_email, user_password, user_apikey_title, user_apikey_public_id,
                                                    user_apikey_secret)
        self._workers_startup = WorkersStartup(subman_bulk_limit, subman_check_period, log_retention_days,
                                               delivery_retention_days)
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
