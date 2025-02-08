from typing import Iterable, Mapping, Type, Any
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import DateTime, UUID, Boolean, Integer

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import OrderBy
from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper
from backend.shared.unit_of_work.change_log import Log
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.subscription import Subscription, SubId, SubscriptionStatus
from backend.subscription.domain.subscription_repo import SubscriptionSby, SubscriptionRepo

subscription_table = Table(
    "subscription",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("plan", JSONB, nullable=False),
    Column("_plan_level", Integer, nullable=False, index=True),
    Column("subscriber_id", String, nullable=False),
    Column("auth_id", UUID, nullable=False),
    Column("status", String, nullable=False),
    Column("last_billing", DateTime(timezone=True), nullable=False),
    Column("paused_from", DateTime(timezone=True), nullable=True),
    Column("autorenew", Boolean, nullable=False),
    Column("usages", JSONB, default=list),
    Column("created_at", DateTime(timezone=True), default=get_current_datetime),
    Column("updated_at", DateTime(timezone=True), default=get_current_datetime),
    Column("fields", JSONB, default=dict),
    Column("_was_deleted", DateTime(timezone=True), default=None, nullable=True),
    Column("_expiration_date", DateTime(timezone=True), nullable=False),
    Column("_earliest_next_renew_in_usages", DateTime(timezone=True), nullable=True),
    Column("_active_status_guard", String, unique=True, nullable=False),
)


class SubscriptionSqlMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Subscription

    def entity_to_mapping(self, entity: Subscription) -> dict:
        result = entity.model_dump(mode="json", exclude={"plan"})
        result["plan"] = entity.plan.model_dump(mode="json")
        result["plan"]["auth_id"] = str(entity.plan.auth_id)
        result["_plan_level"] = entity.plan.level
        result["last_billing"] = entity.last_billing
        result["paused_from"] = entity.paused_from
        result["created_at"] = entity.created_at
        result["updated_at"] = entity.updated_at
        result["auth_id"] = entity.auth_id
        result["_expiration_date"] = entity.expiration_date

        result["_earliest_next_renew_in_usages"] = None if not entity.usages else entity.usages[0].next_renew
        for usage in entity.usages[1:]:
            if usage.next_renew < result["_earliest_next_renew_in_usages"]:
                result["_earliest_next_renew_in_usages"] = usage.next_renew

        result["_active_status_guard"] = (
            str(uuid4())
            if entity.status != SubscriptionStatus.Active
            else f"{entity.subscriber_id}_{entity.auth_id}"
        )
        return result

    def mapping_to_entity(self, data: Mapping) -> Subscription:
        return Subscription(
            id=str(data["id"]),
            plan=data["plan"],
            subscriber_id=data["subscriber_id"],
            auth_id=str(data["auth_id"]),
            status=data["status"],
            last_billing=data["last_billing"],
            paused_from=data["paused_from"],
            autorenew=data["autorenew"],
            usages=data["usages"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            fields=data["fields"]
        )

    def sby_to_filter(self, sby: SubscriptionSby):
        result = []
        if sby.ids:
            result.append(subscription_table.c["id"].in_(sby.ids))
        if sby.auth_ids:
            result.append(subscription_table.c["auth_id"].in_(sby.auth_ids))
        if sby.statuses:
            result.append(subscription_table.c["status"].in_(sby.statuses))
        if sby.subscriber_ids:
            result.append(subscription_table.c["subscriber_id"].in_(sby.subscriber_ids))
        if sby.expiration_date_lt:
            result.append(subscription_table.c["_expiration_date"] < sby.expiration_date_lt)
        if sby.expiration_date_lte:
            result.append(subscription_table.c["_expiration_date"] < sby.expiration_date_lte)
        if sby.expiration_date_gt:
            result.append(subscription_table.c["_expiration_date"] < sby.expiration_date_gt)
        if sby.expiration_date_gte:
            result.append(subscription_table.c["_expiration_date"] < sby.expiration_date_gte)
        if sby.usage_renew_date_lt:
            result.append(subscription_table.c["_earliest_next_renew_in_usages"] < sby.usage_renew_date_lt)
        return result

    def get_orderby(self, orders: OrderBy):
        updated_orders = []
        for pair in orders:
            if pair[0] == "plan.level":
                updated_orders.append(("_plan_level", pair[1]))
            else:
                updated_orders.append(pair)
        return super().get_orderby(updated_orders)


class SqlSubscriptionRepo(SubscriptionRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._base_repo = SqlBaseRepo(session, SubscriptionSqlMapper(subscription_table), subscription_table,
                                      transaction_id)

    async def create_indexes(self):
        pass

    async def add_one(self, item: Subscription) -> None:
        await self._base_repo.add_one(item)

    async def add_many(self, items: Iterable[Subscription]) -> None:
        await self._base_repo.add_many(items)

    async def update_one(self, item: Subscription) -> None:
        await self._base_repo.update_one(item)

    async def get_selected(self, sby: SubscriptionSby, lock: Lock = "write") -> list[Subscription]:
        return await self._base_repo.get_selected(sby)

    async def get_one_by_id(self, sub_id: SubId, lock: Lock = "write") -> Subscription:
        return await self._base_repo.get_one_by_id(sub_id)

    async def get_subscriber_active_one(
            self,
            subscriber_id: str,
            auth_id: AuthId,
            lock: Lock = "write",
    ) -> Optional[Subscription]:
        stmt = (
            subscription_table
            .select()
            .where(
                subscription_table.c["subscriber_id"] == subscriber_id,
                subscription_table.c["_was_deleted"].is_(None),
                # todo надо добавить тест, это интересный баг, когда разные держатели одного подписчика
                subscription_table.c["auth_id"] == auth_id,
                subscription_table.c["status"] == SubscriptionStatus.Active,
            )
            .limit(1)
        )
        result = await self._base_repo.session.execute(stmt)
        record = result.mappings().one_or_none()
        return self._base_repo.mapper.mapping_to_entity(record) if record else None

    async def delete_one(self, item: Subscription) -> None:
        await self._base_repo.delete_one(item)

    async def delete_many(self, items: Iterable[Subscription]) -> None:
        await self._base_repo.delete_many(items)

    def parse_logs(self) -> list[Log]:
        return self._base_repo.parse_logs()
