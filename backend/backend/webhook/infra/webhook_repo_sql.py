from typing import Iterable, Mapping, Type, Any

from sqlalchemy import Table, Column, UUID, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database import metadata
from backend.shared.enums import Lock
from backend.shared.unit_of_work.base_repo_sql import SqlBaseRepo, SQLMapper, AwareDateTime
from backend.shared.utils.dt import get_current_datetime
from backend.webhook.domain.webhook import WebhookId, Webhook
from backend.webhook.domain.webhook_repo import WebhookSby, WebhookRepo

webhook_table = Table(
    'webhook',
    metadata,
    Column('id', UUID, primary_key=True),
    Column('event_code', String, nullable=False),
    Column('target_url', String, nullable=False),
    Column("auth_id", ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
    Column("max_retries", Integer, nullable=False),
    Column("delays", JSONB, nullable=False),
    Column('created_at', AwareDateTime(timezone=True), default=get_current_datetime),
    Column('updated_at', AwareDateTime(timezone=True), default=get_current_datetime),
)


class WebhookSqlMapper(SQLMapper):
    def get_entity_type(self) -> Type[Any]:
        return Webhook

    def entity_to_mapping(self, entity: Webhook) -> dict:
        result = entity.model_dump()
        result["auth_id"] = str(entity.auth_id)
        result["max_retries"] = entity.max_retries
        return result

    def mapping_to_entity(self, data: Mapping) -> Webhook:
        delays = tuple(data["delays"])
        return Webhook(
            id=str(data["id"]),
            delays=delays,
            event_code=data["event_code"],
            target_url=data["target_url"],
            auth_id=str(data["auth_id"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def entity_to_orm_model(self, entity: Webhook):
        raise NotImplemented

    def sby_to_filter(self, sby: WebhookSby):
        result = []
        if sby.ids:
            result.append(webhook_table.c["id"].in_(sby.ids))
        if sby.auth_ids:
            result.append(webhook_table.c["auth_id"].in_(sby.auth_ids))
        if sby.event_codes:
            result.append(webhook_table.c["event_code"].in_(sby.event_codes))
        return result


class SqlWebhookRepo(WebhookRepo):
    def __init__(self, session: AsyncSession, transaction_id: UUID):
        self._base_repo = SqlBaseRepo(session, WebhookSqlMapper(webhook_table), webhook_table,
                                      transaction_id)

    async def add_one(self, item: Webhook) -> None:
        await self._base_repo.add_one(item)

    async def add_many(self, items: Iterable[Webhook]) -> None:
        await self._base_repo.add_many(items)

    async def update_one(self, item: Webhook) -> None:
        await self._base_repo.update_one(item)

    async def get_one_by_id(self, item_id: WebhookId, lock: Lock = "write") -> Webhook:
        return await self._base_repo.get_one_by_id(item_id)

    async def get_selected(self, sby: WebhookSby, lock: Lock = "write") -> list[Webhook]:
        return await self._base_repo.get_selected(sby)

    async def delete_one(self, item: Webhook) -> None:
        await self._base_repo.delete_one(item)

    async def delete_many(self, items: Iterable[Webhook]) -> None:
        await self._base_repo.delete_many(items)

    def parse_logs(self):
        return self._base_repo.parse_logs()
