from typing import Optional, Literal
from uuid import uuid4

from fastapi import Depends, APIRouter, Query
from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.bootstrap import Bootstrap, get_container, auth_closure
from backend.shared.permission_service import PermissionService
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.plan_api import PlanUpdate
from backend.subscription.application.subscription_service import SubscriptionService, SubscriptionPartialUpdateService
from backend.subscription.domain.plan import UsageRate, Usage
from backend.subscription.domain.subscription import (
    Subscription, SubId, SubscriptionStatus, MyBase, )
from backend.subscription.domain.subscription_repo import SubscriptionSby


class SubscriptionCreate(MyBase):
    subscriber_id: str = Field(alias="subscriberId")
    plan: PlanUpdate
    status: SubscriptionStatus = SubscriptionStatus.Active
    created_at: Optional[AwareDatetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[AwareDatetime] = Field(alias="updatedAt", default=None)
    last_billing: Optional[AwareDatetime] = Field(alias="lastBilling", default=None)
    paused_from: Optional[AwareDatetime] = Field(alias="pausedFrom", default=None)
    autorenew: bool = False
    usages: list[Usage] = Field(default_factory=list)

    def to_subscription(self, auth_id: AuthId) -> Subscription:
        created_at = self.created_at if self.created_at else get_current_datetime()
        updated_at = self.updated_at if self.updated_at else created_at
        last_billing = self.last_billing if self.last_billing else created_at
        return Subscription(
            id=uuid4(),
            auth_id=auth_id,
            subscriber_id=self.subscriber_id,
            plan=self.plan.to_plan(auth_id),
            status=self.status,
            created_at=created_at,
            updated_at=updated_at,
            last_billing=last_billing,
            paused_from=self.paused_from,
            autorenew=self.autorenew,
            usages=self.usages,
        )


class SubscriptionUpdate(MyBase):
    id: SubId
    subscriber_id: str = Field(alias="subscriberId")
    plan: PlanUpdate
    status: SubscriptionStatus
    usages: list[UsageRate]
    last_billing: AwareDatetime = Field(alias="lastBilling")
    paused_from: Optional[AwareDatetime] = Field(alias="pausedFrom")
    created_at: AwareDatetime = Field(alias="createdAt")
    updated_at: AwareDatetime = Field(alias="updatedAt", default_factory=get_current_datetime)
    autorenew: bool = False
    usages: list[Usage] = Field(default_factory=list)

    def to_subscription(self, auth_id: AuthId) -> Subscription:
        return Subscription(
            id=self.id,
            auth_id=auth_id,
            subscriber_id=self.subscriber_id,
            plan=self.plan.to_plan(auth_id),
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_billing=self.last_billing,
            paused_from=self.paused_from,
            autorenew=self.autorenew,
            usages=self.usages,
        )

    @classmethod
    def from_subscription(cls, sub: Subscription):
        return cls(**sub.model_dump(exclude={"auth_id", "plan"}), plan=PlanUpdate.from_plan(sub.plan))


subscription_router = APIRouter(
    prefix="/subscription",
    tags=["Subscription"],
)


@subscription_router.post("/")
async def create_subscription(
        data: SubscriptionCreate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Subscription:
    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        subscription = data.to_subscription(auth_user.id)
        subclient = container.subscription_client()
        permission_service = PermissionService(subclient)
        await permission_service.check_auth_user_can_create(subscription, auth_user)
        await permission_service.check_auth_user_can_create(subscription.plan, auth_user)
        service = SubscriptionService(bus, uow)
        await service.create_one(subscription)
        await service.send_events()
        await uow.commit()
        return await uow.subscription_repo().get_one_by_id(subscription.id)


@subscription_router.get("/")
async def get_selected(
        ids: Optional[set[SubId]] = Query(None),
        statuses: Optional[set[SubscriptionStatus]] = Query(None),
        subscriber_ids: Optional[set[str]] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        order_by: list[str] = Query(["created_at"]),
        asc: Literal[1, -1] = Query(1),
        container: Bootstrap = Depends(get_container),
        auth_user=Depends(auth_closure),
) -> list[Subscription]:
    sby = SubscriptionSby(
        ids=set(ids) if ids else None,
        statuses=set(statuses) if statuses else None,
        auth_ids={auth_user.id},
        subscriber_ids=set(subscriber_ids) if subscriber_ids else None,
        skip=skip,
        limit=limit,
        order_by=[(field, asc) for field in order_by]
    )
    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_get_many(sby, auth_user)
        return await SubscriptionService(bus, uow).get_selected(sby)


@subscription_router.get("/{sub_id}")
async def get_subscription_by_id(
        sub_id: SubId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Subscription:
    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        subclient = container.subscription_client()
        result = await SubscriptionService(bus, uow).get_one_by_id(sub_id)
        await PermissionService(subclient).check_auth_user_can_get(result, auth_user)
        return result


@subscription_router.get("/active-one/{subscriber_id}")
async def get_active_one(
        subscriber_id: str,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Optional[Subscription]:
    async with container.unit_of_work_factory().create_uow() as uow:
        result = await uow.subscription_repo().get_subscriber_active_one(subscriber_id, auth_user.id)
        return result


@subscription_router.delete("/{sub_id}")
async def delete_one_by_id(
        sub_id: SubId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        bus = container.eventbus()
        subclient = container.subscription_client()
        result = await SubscriptionService(bus, uow).get_one_by_id(sub_id)
        await PermissionService(subclient).check_auth_user_can_delete(result, auth_user)
        service = SubscriptionService(bus, uow)
        await service.delete_one(result)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.delete("/")
async def delete_selected(
        sby: SubscriptionSby,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        sby.auth_ids = {auth_user.id}
        bus = container.eventbus()
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_delete_many(sby, auth_user)
        service = SubscriptionService(bus, uow)
        await service.delete_selected(sby)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.put("/{sub_id}")
async def update_subscription(
        subscription: SubscriptionUpdate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        subscription = subscription.to_subscription(auth_user.id)
        bus = container.eventbus()
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(subscription, auth_user)
        service = SubscriptionService(bus, uow)
        await service.update_one(subscription)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/increase-usage")
async def increase_usages(
        sub_id: SubId,
        code: str,
        value: float,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.increase_usage(target_sub, code, value)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/add-usages")
async def add_usages(
        sub_id: SubId,
        usages: list[Usage],
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.add_usages(target_sub, usages)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/remove-usages")
async def remove_usages(
        sub_id: SubId,
        codes: list[str],
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.remove_usages(target_sub, codes)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/update-usages")
async def update_usages(
        sub_id: SubId,
        usages: list[Usage],
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.update_usages(target_sub, usages)
        await uow.commit()
        await service.send_events()
        return "Ok"


@subscription_router.patch("/{sub_id}/update-plan")
async def update_plan(
        sub_id: SubId,
        plan: PlanUpdate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        plan = plan.to_plan(auth_user.id)
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.update_plan(target_sub, plan)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/pause")
async def pause_subscription(
        sub_id: SubId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.pause_sub(target_sub)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/resume")
async def resume_subscription(
        sub_id: SubId,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.resume_sub(target_sub)
        await service.send_events()
        await uow.commit()
        return "Ok"


@subscription_router.patch("/{sub_id}/renew")
async def renew_subscription(
        sub_id: SubId,
        from_date: AwareDatetime = None,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        subclient = container.subscription_client()
        await PermissionService(subclient).check_auth_user_can_update(target_sub, auth_user)
        service = SubscriptionPartialUpdateService(container.eventbus(), uow)
        await service.renew_sub(target_sub, from_date)
        await service.send_events()
        await uow.commit()
        return "Ok"
