import uuid
from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Column, String, Float, Integer, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper, AwareDateTime
from backend.shared.unit_of_work.change_log import Log
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Cycle
from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.plan_repo import PlanRepo, PlanSby

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
    Column('auth_id', UUID(as_uuid=True), nullable=False),
    Column('discounts', JSONB, default=list),
    Column('created_at', AwareDateTime(timezone=True), default=get_current_datetime),
    Column('updated_at', AwareDateTime(timezone=True), default=get_current_datetime),
)


class PlanSqlMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Plan

    def entity_to_mapping(self, entity: Plan, uuid_as_str=False, as_json=False) -> dict:
        result = entity.model_dump(mode="json")
        result["auth_id"] = entity.auth_id
        result["created_at"] = entity.created_at
        result["updated_at"] = entity.updated_at
        result["billing_cycle"] = entity.billing_cycle.code
        return result

    def mapping_to_entity(self, data: Mapping) -> Plan:
        billing_cycle = Cycle.from_code(data["billing_cycle"])
        return Plan(
            id=str(data["id"]),
            title=data["title"],
            price=data["price"],
            currency=data["currency"],
            billing_cycle=billing_cycle,
            description=data["description"],
            level=data["level"],
            features=data["features"],
            usage_rates=data["usage_rates"],
            fields=data["fields"],
            auth_id=str(data["auth_id"]),
            discounts=data["discounts"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def entity_to_orm_model(self, entity: Plan):
        raise NotImplemented

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

    async def create_indexes(self):
        pass

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
