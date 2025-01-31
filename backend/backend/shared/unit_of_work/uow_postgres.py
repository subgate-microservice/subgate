from typing import Self, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from backend.auth.domain.apikey_repo import ApikeyRepo
from backend.auth.infra.repositories.apikey_repo_sql import SqlApikeyRepo
from backend.shared.unit_of_work.change_log import ChangeLog
from backend.shared.unit_of_work.sql_statement_parser import SqlStatementBuilder
from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.subscription.domain.plan_repo import PlanRepo
from backend.subscription.domain.subscription_repo import SubscriptionRepo
from backend.subscription.infra.plan_repo_sql import SqlPlanRepo
from backend.subscription.infra.subscription_repo_sql import SqlSubscriptionRepo
from backend.webhook.domain.telegram import TelegramRepo
from backend.webhook.domain.webhook_repo import WebhookRepo
from backend.webhook.infra.telegram_repo_sql import SqlTelegramRepo
from backend.webhook.infra.webhook_repo_sql import SqlWebhookRepo


class NewUow(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._change_log: Optional[ChangeLog] = None
        self._session: Optional[AsyncSession] = None
        self._repos = {}

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self._change_log = ChangeLog()
        self._repos = {
            "plan_repo": SqlPlanRepo(self._session, self._change_log),
            "webhook_repo": SqlWebhookRepo(self._session, self._change_log),
            "subscription_repo": SqlSubscriptionRepo(self._session, self._change_log),
            "telegram_repo": SqlTelegramRepo(self._session, self._change_log),
            "apikey_repo": SqlApikeyRepo(self._session, self._change_log),
        }
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._repos = {}
        await self._session.close()
        self._session = None
        self._change_log = None

    async def commit(self):
        logs = self._change_log.get_uncommitted()
        try:
            statements = SqlStatementBuilder().load_logs(logs).parse_action_statements()

            for stmt, data in statements:
                await self._session.execute(stmt, data)
            await self._session.commit()
            for log in logs:
                self._change_log.change_status(log.id, "committed")
        except Exception as err:
            await self._session.rollback()
            for log in logs:
                self._change_log.change_status(log.id, "reverted")
            raise err

    async def rollback(self):
        try:
            logs = self._change_log.get_committed()
            statements = SqlStatementBuilder().load_logs(logs).parse_rollback_statements()

            for stmt, data in statements:
                await self._session.execute(stmt, data)
            await self._session.commit()
            for log in logs:
                self._change_log.change_status(log.id, "revert_error")
        except Exception as err:
            await self._session.rollback()
            raise err

    def subscription_repo(self) -> SubscriptionRepo:
        return self._repos["subscription_repo"]

    def plan_repo(self) -> PlanRepo:
        return self._repos["plan_repo"]

    def webhook_repo(self) -> WebhookRepo:
        return self._repos["webhook_repo"]

    def apikey_repo(self) -> ApikeyRepo:
        return self._repos["apikey_repo"]

    def telegram_repo(self) -> TelegramRepo:
        return self._repos["telegram_repo"]


class SqlUowFactory(UnitOfWorkFactory):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    def create_uow(self) -> UnitOfWork:
        return NewUow(self._session_factory)
