from typing import Iterable, Mapping, Type, Any
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import UUID, Boolean, Integer, Float

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import OrderBy
from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper, AwareDateTime
from backend.shared.unit_of_work.change_log import Log
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.subscription import Subscription, SubId, SubscriptionStatus, BillingInfo, PlanInfo
from backend.subscription.domain.subscription_repo import SubscriptionSby, SubscriptionRepo
from backend.subscription.infra.deserializers import deserialize_uuid, deserialize_datetime
from backend.subscription.infra.serializers import serialize_subscription

subscription_table = Table(
    "subscription",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("subscriber_id", String, nullable=False),
    Column("pi_id", UUID, nullable=False),
    Column("pi_title", String, nullable=False),
    Column("pi_description", String, nullable=True),
    Column("pi_level", Integer, nullable=False),
    Column("pi_features", String, nullable=True),
    Column("bi_price", Float, nullable=False),
    Column("bi_currency", String, nullable=False),
    Column("bi_billing_cycle", String, nullable=False),
    Column("bi_last_billing", AwareDateTime, nullable=False),
    Column("auth_id", UUID, nullable=False),
    Column("status", String, nullable=False),
    Column("paused_from", AwareDateTime(timezone=True), nullable=True),
    Column("autorenew", Boolean, nullable=False),
    Column("usages", JSONB, default=list),
    Column("discounts", JSONB, default=list),
    Column("created_at", AwareDateTime(timezone=True), default=get_current_datetime),
    Column("updated_at", AwareDateTime(timezone=True), default=get_current_datetime),
    Column("fields", JSONB, default=dict),
    Column("_expiration_date", AwareDateTime(timezone=True), nullable=False),
    Column("_earliest_next_renew_in_usages", AwareDateTime(timezone=True), nullable=True),
    Column("_active_status_guard", String, unique=True, nullable=False),
)


class SubscriptionSqlMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Subscription

    def entity_to_mapping(self, entity: Subscription) -> dict:
        mapping = serialize_subscription(entity)
        plan_info = {f"pi_{key}": value for key, value in mapping.pop("plan_info").items()}
        billing_info = {f"bi_{key}": value for key, value in mapping.pop("billing_info").items()}
        mapping = mapping | plan_info | billing_info

        mapping["_expiration_date"] = entity.expiration_date
        usages = entity.usages.get_all()
        mapping["_earliest_next_renew_in_usages"] = None if not usages else usages[0].next_renew
        for usage in usages[1:]:
            if usage.next_renew < mapping["_earliest_next_renew_in_usages"]:
                mapping["_earliest_next_renew_in_usages"] = usage.next_renew

        mapping["_active_status_guard"] = (
            str(uuid4())
            if entity.status != SubscriptionStatus.Active
            else f"{entity.subscriber_id}_{entity.auth_id}"
        )
        return mapping

    def mapping_to_entity(self, data: Mapping) -> Subscription:
        plan_info = PlanInfo(
            id=deserialize_uuid(data["pi_id"]),
            title=data["pi_title"],
            description=data["pi_description"],
            level=data["pi_level"],
            features=data["pi_features"]
        )
        billing_info = BillingInfo(
            price=data["bi_price"],
            currency=data["bi_currency"],
            billing_cycle=Period(data["bi_billing_cycle"]),
            last_billing=deserialize_datetime(data["bi_last_billing"]),
        )
        return Subscription.create_unsafe(
            id=deserialize_uuid(data["id"]),
            plan_info=plan_info,
            billing_info=billing_info,
            subscriber_id=data["subscriber_id"],
            auth_id=deserialize_uuid(data["auth_id"]),
            status=data["status"],
            paused_from=data["paused_from"],
            autorenew=data["autorenew"],
            usages=data["usages"],
            discounts=data["discounts"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            fields=data["fields"],
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
            if pair[0] == "plan_info.level":
                updated_orders.append(("pi_level", pair[1]))
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
