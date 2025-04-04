import uuid
from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Column, String, Float, Integer, Table, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper, AwareDateTime
from backend.shared.unit_of_work.change_log import Log
from backend.shared.utils.dt import get_current_datetime
from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.plan_repo import PlanRepo, PlanSby
from backend.subscription.infra.deserializers import deserialize_plan
from backend.subscription.infra.serializers import serialize_plan

plan_table = Table(
    'plan',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=str(uuid.uuid4())),
    Column('title', String, nullable=False),
    Column('price', Float, nullable=False),
    Column('currency', String, nullable=False),
    Column('billing_cycle', String, nullable=False),
    Column('description', String, default=None, nullable=True),
    Column('level', Integer, default=1),
    Column('features', String, nullable=True),
    Column('usage_rates', JSONB, default=list),
    Column('fields', JSONB, default=dict),
    Column("auth_id", ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
    Column('discounts', JSONB, default=list),
    Column('created_at', AwareDateTime(timezone=True), default=get_current_datetime),
    Column('updated_at', AwareDateTime(timezone=True), default=get_current_datetime),
)


class PlanSqlMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Plan

    def entity_to_mapping(self, entity: Plan, uuid_as_str=False, as_json=False) -> dict:
        return serialize_plan(entity)

    def mapping_to_entity(self, data: Mapping) -> Plan:
        return deserialize_plan(data)

    def sby_to_filter(self, sby: PlanSby):
        result = []
        if sby.ids:
            cond = plan_table.c["id"].in_(sby.ids)
            result.append(cond)
        if sby.auth_ids:
            cond = plan_table.c["auth_id"].in_(sby.auth_ids)
            result.append(cond)
        return result


class SqlPlanRepo(PlanRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._base_repo = SqlBaseRepo(session, PlanSqlMapper(plan_table), plan_table, transaction_id)

    async def add_one(self, item: Plan) -> None:
        await self._base_repo.add_one(item)

    async def add_many(self, items: Iterable[Plan]) -> None:
        for item in items:
            await self.add_one(item)

    async def update_one(self, item: Plan) -> None:
        await self._base_repo.update_one(item)

    async def get_one_by_id(self, item_id: PlanId, lock: Lock = "write") -> Plan:
        return await self._base_repo.get_one_by_id(item_id)

    async def get_selected(self, sby: PlanSby, lock: Lock = "write") -> list[Plan]:
        return await self._base_repo.get_selected(sby)

    async def delete_one(self, item: Plan) -> None:
        await self._base_repo.delete_one(item)

    async def delete_many(self, items: Iterable[Plan]) -> None:
        for item in items:
            await self.delete_one(item)

    def parse_logs(self) -> list[Log]:
        return self._base_repo.parse_logs()
