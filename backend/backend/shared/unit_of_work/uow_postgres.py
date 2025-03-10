from typing import Self, Optional
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from backend.auth.domain.apikey import ApikeyRepo
from backend.auth.infra.apikey.apikey_repo_sql import SqlApikeyRepo, apikey_table
from backend.shared.event_driven.base_event import Event
from backend.shared.unit_of_work.change_log import SqlLogRepo, LogConverter
from backend.shared.unit_of_work.sql_statement_parser import SqlStatementBuilder
from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.subscription.domain.exceptions import ActiveStatusConflict
from backend.subscription.domain.plan_repo import PlanRepo
from backend.subscription.domain.subscription_repo import SubscriptionRepo
from backend.subscription.infra.plan_repo_sql import SqlPlanRepo, plan_table
from backend.subscription.infra.subscription_repo_sql import SqlSubscriptionRepo, subscription_table
from backend.webhook.domain.delivery_task import DeliveryTaskRepo
from backend.webhook.domain.webhook_repo import WebhookRepo
from backend.webhook.infra.delivery_task_repo_sql import SqlDeliveryTaskRepo, delivery_task_table
from backend.webhook.infra.webhook_repo_sql import SqlWebhookRepo, webhook_table


def convert_error(err: Exception) -> Exception:
    if isinstance(err, IntegrityError):
        error_string = str(err.__dict__["orig"])
        if "Key (_active_status_guard)=" in error_string:
            subscriber_id = error_string.split("Key (_active_status_guard)=(")[1].split("_")[0]
            err = ActiveStatusConflict(subscriber_id)
    return err


TABLES = {
    plan_table.name: plan_table,
    webhook_table.name: webhook_table,
    subscription_table.name: subscription_table,
    delivery_task_table.name: delivery_task_table,
    apikey_table.name: apikey_table,
}


class NewUow(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._transaction_id = None
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self._repos = {}
        self._log_repo: Optional[SqlLogRepo] = None
        self._events = []

    async def __aenter__(self) -> Self:
        self._transaction_id = uuid4()
        self._session = self._session_factory()
        self._log_repo = SqlLogRepo(self._session)
        self._repos = {
            "plan_repo": SqlPlanRepo(self._session, self._transaction_id),
            "webhook_repo": SqlWebhookRepo(self._session, self._transaction_id),
            "subscription_repo": SqlSubscriptionRepo(self._session, self._transaction_id),
            "delivery_task_repo": SqlDeliveryTaskRepo(self._session, self._transaction_id),
            "apikey_repo": SqlApikeyRepo(self._session)
        }
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._repos = {}
        await self._session.close()
        self._session = None
        self._transaction_id = None

    def push_event(self, event: Event) -> None:
        self._events.append(event)

    def parse_events(self) -> list[Event]:
        events = self._events
        self._events = []
        return events

    async def commit(self):
        try:
            logs = []
            for repo in self._repos.values():
                if hasattr(repo, "parse_logs"):
                    logs.extend(repo.parse_logs())
            statements = SqlStatementBuilder(TABLES).load_logs(logs).parse_action_statements()

            # Выполняем запросы к базе
            for stmt, data in statements:
                await self._session.execute(stmt, data) if data else await self._session.execute(stmt)

            # Сохраняем логи
            await self._log_repo.add_many_logs(logs)

            await self._session.commit()
        except Exception as err:
            await self._session.rollback()
            err = convert_error(err)
            raise err

    async def rollback(self):
        try:
            current_logs = await self._log_repo.get_logs_by_transaction_id(self._transaction_id)

            model_ids = [x.model_id for x in current_logs]
            previous_logs = await self._log_repo.get_previous_logs(model_ids, self._transaction_id)
            rollback_logs = LogConverter(current_logs, previous_logs, self._transaction_id).convert()

            statements = SqlStatementBuilder(TABLES).load_logs(rollback_logs).parse_rollback_statements()

            for stmt, data in statements:
                await self._session.execute(stmt, data) if data else await self._session.execute(stmt)

            await self._log_repo.add_many_logs(rollback_logs)

            await self._session.commit()
        except Exception as err:
            await self._session.rollback()
            err = convert_error(err)
            raise err

    def subscription_repo(self) -> SubscriptionRepo:
        return self._repos["subscription_repo"]

    def plan_repo(self) -> PlanRepo:
        return self._repos["plan_repo"]

    def webhook_repo(self) -> WebhookRepo:
        return self._repos["webhook_repo"]

    def delivery_task_repo(self) -> DeliveryTaskRepo:
        return self._repos["delivery_task_repo"]

    def apikey_repo(self) -> ApikeyRepo:
        return self._repos["apikey_repo"]


class SqlUowFactory(UnitOfWorkFactory):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    def create_uow(self) -> UnitOfWork:
        return NewUow(self._session_factory)
