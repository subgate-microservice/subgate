import datetime
from abc import abstractmethod
from typing import Any, Protocol, Mapping, Type
from typing import Iterable, Hashable
from uuid import UUID

from sqlalchemy import Table, TypeDecorator, DateTime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.base_models import BaseSby, OrderBy
from backend.shared.enums import Lock
from backend.shared.exceptions import ItemNotExist
from backend.shared.unit_of_work.change_log import Log
from backend.shared.utils.dt import get_current_datetime


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


class HasId(Protocol):
    id: UUID


class SqlBaseRepo:
    def __init__(
            self,
            session: AsyncSession,
            mapper: SQLMapper,
            table: Table,
            transaction_id: UUID,
    ):
        self.session = session
        self.mapper = mapper
        self.table = table
        self._transaction_id = transaction_id
        self._logs = []

    async def add_one(self, item: HasId) -> None:
        data = self.mapper.entity_to_mapping(item)
        self._logs.append(
            Log(
                collection_name=self.table.name,
                action="insert",
                model_state=data,
                created_at=get_current_datetime(),
                transaction_id=self._transaction_id,
                model_id=item.id,
            )
        )

    async def add_many(self, items: Iterable[Any]) -> None:
        for item in items:
            await self.add_one(item)

    async def update_one(self, item: HasId) -> None:
        new_item = self.mapper.entity_to_mapping(item)
        self._logs.append(
            Log(
                collection_name=self.table.name,
                action="update",
                model_state=new_item,
                created_at=get_current_datetime(),
                transaction_id=self._transaction_id,
                model_id=item.id,
            )
        )

    async def delete_one(self, item: HasId) -> None:
        self._logs.append(
            Log(
                collection_name=self.table.name,
                action="delete",
                model_state=None,
                created_at=get_current_datetime(),
                transaction_id=self._transaction_id,
                model_id=item.id,
            )
        )

    async def delete_many(self, items: Iterable[HasId]) -> None:
        for item in items:
            await self.delete_one(item)

    async def _get_one_by_id(self, item_id: Hashable, lock: Lock = "write") -> Mapping:
        query = (
            self.table
            .select()
            .where(self.table.c["id"] == item_id)
            .limit(1)
        )
        if lock == "write":
            query = query.with_for_update()
        elif lock == "read":
            raise NotImplemented

        result = await self.session.execute(query)

        record = result.mappings().one_or_none()
        if not record:
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
            .where(*filter_by)
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

    def parse_logs(self):
        result = self._logs
        self._logs = []
        return result


class AwareDateTime(TypeDecorator):
    """Преобразует ISO 8601 строки в datetime.datetime при вставке в БД"""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Преобразует входящее значение перед записью в БД"""
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value)
        return value  # Оставляем datetime как есть

    def process_result_value(self, value, dialect):
        """Возвращает datetime в Python"""
        return value  # SQLAlchemy уже возвращает datetime, ничего менять не нужно
