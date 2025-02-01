from abc import abstractmethod
from types import MappingProxyType
from typing import Any, Protocol, Mapping, Type, Optional
from typing import Iterable, Hashable
from uuid import uuid4

from loguru import logger
from sqlalchemy import MetaData, Table, Column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend import config
from backend.shared.base_models import BaseSby, OrderBy
from backend.shared.enums import Lock
from backend.shared.exceptions import ItemNotExist
from backend.shared.unit_of_work.change_log import ChangeLog, Log
from backend.shared.utils import get_current_datetime


class SQLMapper:
    def __init__(self, table: Table):
        self.table = table

    @abstractmethod
    def get_entity_type(self) -> Type[Any]:
        raise NotImplemented

    @abstractmethod
    def entity_to_mapping(self, entity: Any) -> dict:
        raise NotImplemented

    @abstractmethod
    def mapping_to_entity(self, mapping: Mapping) -> Any:
        raise NotImplemented

    @abstractmethod
    def sby_to_filter(self, sby: BaseSby) -> Any:
        raise NotImplemented

    def get_orderby(self, orders: OrderBy):
        order_clauses = []

        for column_name, direction in orders:
            column = self.table.c.get(column_name)
            if column is None:
                raise ValueError(f"Column '{column_name}' not found in table '{self.table.name}'")
            if direction == 1:
                pass
            elif direction == -1:
                column = column.desc()
            else:
                raise ValueError()
            order_clauses.append(column)
        return order_clauses


metadata = MetaData()


async def drop_and_create_postgres_tables():
    async_engine = create_async_engine(config.POSTGRES_URL, echo=False)
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
        await conn.commit()
    logger.info("Postgres tables were successfully created.")


class HasId(Protocol):
    id: Hashable


class SqlBaseRepo:
    def __init__(
            self,
            session: AsyncSession,
            mapper: SQLMapper,
            table: Table,
            change_log: ChangeLog
    ):
        self.session = session
        self.mapper = mapper
        self.table = table
        self._change_log = change_log

    async def add_one(self, item: HasId) -> None:
        data = self.mapper.entity_to_mapping(item)
        data["_was_deleted"] = None
        self._change_log.append(
            Log(
                id=str(uuid4()),
                collection_name=self.table.name,
                action="insert",
                action_data=data,
                rollback_data=None,
                status="uncommitted",
                created_at=get_current_datetime(),
            )
        )

    async def add_many(self, items: Iterable[Any]) -> None:
        for item in items:
            await self.add_one(item)

    async def update_one(self, item: HasId) -> None:
        old_item = MappingProxyType(await self._get_one_by_id(item.id))
        item = self.mapper.entity_to_mapping(item)
        self._change_log.append(
            Log(
                id=str(uuid4()),
                collection_name=self.table.name,
                action="update",
                action_data=item,
                rollback_data=old_item,
                status="uncommitted",
                created_at=get_current_datetime(),
            )
        )

    async def delete_one(self, item: HasId) -> None:
        self._change_log.append(
            Log(
                id=str(uuid4()),
                collection_name=self.table.name,
                action="safe_delete",
                action_data={"id": item.id},
                rollback_data={"id": item.id},
                status="uncommitted",
                created_at=get_current_datetime(),
            )
        )

    async def delete_many(self, items: Iterable[HasId]) -> None:
        for item in items:
            await self.delete_one(item)

    async def _get_one_by_id(self, item_id: Hashable, lock: Lock = "write") -> Mapping:
        query = (
            self.table
            .select()
            .where(self.table.c["id"] == item_id, self.table.c["_was_deleted"].is_(None))
            .limit(1)
        )
        if lock == "write":
            query = query.with_for_update()
        elif lock == "read":
            raise NotImplemented

        result = await self.session.execute(query)

        record = result.mappings().one_or_none()
        if not record or record.get("_was_deleted"):
            raise ItemNotExist(item_type=self.mapper.get_entity_type(), lookup_field_value=item_id)

        return record

    async def get_one_by_id(self, item_id: Hashable, lock: Lock = "write") -> Any:
        record = await self._get_one_by_id(item_id, lock)
        return self.mapper.mapping_to_entity(record)

    async def get_selected(self, sby, lock: Lock = "write") -> list[Any]:
        filter_by = self.mapper.sby_to_filter(sby)
        query = (
            self.table
            .select()
            .where(*filter_by, self.table.c["_was_deleted"].is_(None))
            .offset(sby.skip)
            .limit(sby.limit)
        )

        if lock == "write":
            query = query.with_for_update()
        elif lock == "read":
            raise NotImplemented

        query = query.order_by(*self.mapper.get_orderby(sby.order_by))
        result = await self.session.execute(query)
        plans = [self.mapper.mapping_to_entity(mapping) for mapping in result.mappings()]
        return plans
