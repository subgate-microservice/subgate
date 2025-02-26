from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import Bootstrap, get_container, auth_closure
from backend.webhook.adapters.schemas import WebhookCreate, WebhookUpdate
from backend.webhook.application import usecases
from backend.webhook.domain.webhook import Webhook, WebhookId
from backend.webhook.domain.webhook_repo import WebhookSby

webhook_router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"],
)


@webhook_router.post("/")
async def create_one(
        webhook_create: WebhookCreate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        webhook = webhook_create.to_webhook(auth_user.id)
        create_webhook_usecase = usecases.CreateWebhook(uow)
        await create_webhook_usecase.execute(webhook)
        await uow.commit()
    return "Ok"


@webhook_router.get("/{webhook_id}")
async def get_one_by_id(
        webhook_id: WebhookId,
        container: Bootstrap = Depends(get_container),
) -> Webhook:
    async with container.unit_of_work_factory().create_uow() as uow:
        return await uow.webhook_repo().get_one_by_id(webhook_id)


@webhook_router.get("/")
async def get_selected(
        ids: Optional[list[WebhookId]] = Query(None),
        event_codes: Optional[list[str]] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        order_by: list[str] = Query(["created_at"]),
        asc: bool = Query(True),
        auth_user=Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> list[Webhook]:
    sby = WebhookSby(
        ids=set(ids) if ids else None,
        auth_ids={auth_user.id},
        event_codes=set(event_codes) if event_codes else None,
        skip=skip,
        limit=limit,
        order_by=[(field, 1 if asc else -1) for field in order_by],
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        return await uow.webhook_repo().get_selected(sby)


@webhook_router.put("/{webhook_id}")
async def update_one(
        webhook: WebhookUpdate,
        auth_user=Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        target = await uow.webhook_repo().get_one_by_id(webhook.id)
        webhook = webhook.to_webhook(auth_user.id, target.created_at)
        usecase = usecases.UpdateWebhook(uow)
        await usecase.execute(webhook)
        await uow.commit()
    return "Ok"


@webhook_router.delete("/{webhook_id}")
async def delete_one_by_id(
        webhook_id: WebhookId,
        _auth_user=Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        await usecases.DeleteWebhookById(uow).execute(webhook_id)
        await uow.commit()
    return "Ok"


@webhook_router.delete("/")
async def delete_selected(
        ids: Optional[list[WebhookId]] = Query(None),
        event_codes: Optional[list[str]] = Query(None),
        auth_user=Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        sby = WebhookSby(
            ids=ids,
            event_codes=event_codes,
            auth_ids={auth_user.id}
        )
        await usecases.DeleteSelectedWebhooks(uow).execute(sby)
        await uow.commit()
    return "Ok"
