from typing import Optional, Self

from fastapi import APIRouter, Depends, Query
from pydantic import Field, AwareDatetime, model_validator

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container, Bootstrap, auth_closure
from backend.shared.exceptions import ValidationError
from backend.shared.permission_service import PermissionService
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.plan_schemas import PlanCreate
from backend.subscription.application.plan_service import PlanService
from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.plan_repo import PlanSby


class PlanUpdate(PlanCreate):
    id: PlanId
    created_at: AwareDatetime
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)

    @classmethod
    def from_plan(cls, plan: Plan):
        return cls(**plan.model_dump(exclude={"auth_id"}))

    @model_validator(mode="after")
    def _validate_other(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValidationError(
                field="updated_at",
                value=self.updated_at.isoformat(),
                value_type=self.updated_at.__class__.__name__,
                message="updated_at earlier than created_at"
            )
        return self


plan_router = APIRouter(
    prefix="/plan",
    tags=["Plan"],
)


@plan_router.post("/")
async def create_one(
        data: PlanCreate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Plan:
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = data.to_plan(auth_user.id)
        subclient = container.subscription_client()
        bus = container.eventbus()
        await PermissionService(subclient).check_auth_user_can_create(plan, auth_user)
        await PlanService(bus, uow).create_one(plan)
        await uow.commit()
        return plan


@plan_router.get("/{plan_id}")
async def get_one_by_id(
        plan_id: PlanId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Plan:
    async with container.unit_of_work_factory().create_uow() as uow:
        subclient = container.subscription_client()
        bus = container.eventbus()
        result = await PlanService(bus, uow).get_one_by_id(plan_id)
        await PermissionService(subclient).check_auth_user_can_get(result, auth_user)
        return result


@plan_router.get("/")
async def get_selected(
        ids: Optional[list[PlanId]] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        order_by: Optional[list[str]] = Query(["created_at,1"]),
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),

) -> list[Plan]:
    order_by = [(x.split(",")[0], x.split(",")[1]) for x in order_by]
    sby = PlanSby(
        ids=set(ids) if ids else None,
        auth_ids={auth_user.id},
        skip=skip,
        limit=limit,
        order_by=order_by,
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        subclient = container.subscription_client()
        bus = container.eventbus()
        await PermissionService(subclient).check_auth_user_can_get_many(sby, auth_user)
        return await PlanService(bus, uow).get_selected(sby)


@plan_router.put("/{plan_id}")
async def update_one(
        plan: PlanUpdate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        subclient = container.subscription_client()
        bus = container.eventbus()
        plan = plan.to_plan(auth_user.id)
        await PermissionService(subclient).check_auth_user_can_update(plan, auth_user)
        await PlanService(bus, uow).update_one(plan)
        await uow.commit()
        return "Ok"


@plan_router.delete("/{plan_id}")
async def delete_one(
        plan_id: PlanId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        subclient = container.subscription_client()
        bus = container.eventbus()
        plan_service = PlanService(bus, uow)
        target = await plan_service.get_one_by_id(plan_id)
        await PermissionService(subclient).check_auth_user_can_delete(target, auth_user)
        await plan_service.delete_one(target)
        await uow.commit()
        return "Ok"


@plan_router.delete("/")
async def delete_selected(
        sby: PlanSby,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        subclient = container.subscription_client()
        bus = container.eventbus()
        sby.auth_ids = {auth_user.id}
        await PermissionService(subclient).check_auth_user_can_delete_many(sby, auth_user)
        await PlanService(bus, uow).delete_selected(sby)
        await uow.commit()
        return "Ok"
