from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container, Bootstrap, auth_closure
from backend.subscription.adapters.schemas import PlanCreate, PlanUpdate, PlanRetrieve
from backend.subscription.application.plan_usecases import create_plan, save_updated_plan, delete_plan
from backend.subscription.domain.plan import PlanId, PlanUpdater
from backend.subscription.domain.plan_repo import PlanSby

plan_router = APIRouter(
    prefix="/plan",
    tags=["Plan"],
)


@plan_router.post("/")
async def create_one(
        plan_create: PlanCreate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = plan_create.to_plan(auth_user.id)
        await create_plan(plan, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    container.telegraph().wake_worker()
    return "Ok"


@plan_router.get("/{plan_id}")
async def get_one_by_id(
        plan_id: PlanId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> PlanRetrieve:
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = await uow.plan_repo().get_one_by_id(plan_id)
        plan_retrieve = PlanRetrieve.from_plan(plan)
        return plan_retrieve


@plan_router.get("/")
async def get_selected(
        ids: Optional[list[PlanId]] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        order_by: Optional[list[str]] = Query(["created_at,1"]),
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),

) -> list[PlanRetrieve]:
    order_by = [(x.split(",")[0], x.split(",")[1]) for x in order_by]
    sby = PlanSby(
        ids=set(ids) if ids else None,
        auth_ids={auth_user.id},
        skip=skip,
        limit=limit,
        order_by=order_by,
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        plans = await uow.plan_repo().get_selected(sby)
        plan_retrieves = [PlanRetrieve.from_plan(x) for x in plans]
        return plan_retrieves


@plan_router.put("/{plan_id}")
async def update_one(
        plan_update: PlanUpdate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    # todo мы здесь не проверяем auth_id - надо поправить
    async with container.unit_of_work_factory().create_uow() as uow:
        old_version = await uow.plan_repo().get_one_by_id(plan_update.id)
        new_version = plan_update.to_plan(auth_user.id, old_version.created_at)
        PlanUpdater(old_version, new_version).update()
        await save_updated_plan(old_version, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    container.telegraph().wake_worker()
    return "Ok"


@plan_router.delete("/{plan_id}")
async def delete_one(
        plan_id: PlanId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        target_plan = await uow.plan_repo().get_one_by_id(plan_id)
        await delete_plan(target_plan, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    container.telegraph().wake_worker()
    return "Ok"


@plan_router.delete("/")
async def delete_selected(
        ids: Optional[set[PlanId]] = Query(None),
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        sby = PlanSby(ids=ids, auth_ids={auth_user.id})
        targets = await uow.plan_repo().get_selected(sby)
        for target in targets:
            await delete_plan(target, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    container.telegraph().wake_worker()
    return "Ok"
