from typing import Optional

from fastapi import Depends, APIRouter, Query
from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthUser, AuthId
from backend.bootstrap import Bootstrap, get_container, auth_closure
from backend.shared.permission_service import PermissionService
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.plan_api import PlanUpdate
from backend.subscription.adapters.subscription_schemas import SubscriptionCreate
from backend.subscription.application.subscription_service import SubscriptionService, SubscriptionPartialUpdateService
from backend.subscription.domain.plan import UsageRate, Usage
from backend.subscription.domain.subscription import (
    Subscription, SubId, SubscriptionStatus, MyBase, )
from backend.subscription.domain.subscription_repo import SubscriptionSby


class SubscriptionUpdate(MyBase):
    id: SubId
    subscriber_id: str
    plan: PlanUpdate
    status: SubscriptionStatus
    usages: list[UsageRate]
    last_billing: AwareDatetime
    paused_from: Optional[AwareDatetime]
    created_at: AwareDatetime
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)
    autorenew: bool = False
    usages: list[Usage]
    fields: dict

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
            fields=self.fields,
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
        subscription_create: SubscriptionCreate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Subscription:
    # todo вернуть permission service
    async with container.unit_of_work_factory().create_uow() as uow:
        subscription = subscription_create.to_subscription(auth_user.id)
        service = SubscriptionService(container.eventbus(), uow)
        await service.create_one(subscription)
        await service.send_events()
        await uow.commit()
        return await uow.subscription_repo().get_one_by_id(subscription.id)


@subscription_router.get("/")
async def get_selected(
        ids: Optional[set[SubId]] = Query(None),
        statuses: Optional[set[SubscriptionStatus]] = Query(None),
        subscriber_ids: Optional[set[str]] = Query(None),
        expiration_date_lt: Optional[AwareDatetime] = Query(None),
        expiration_date_lte: Optional[AwareDatetime] = Query(None),
        expiration_date_gt: Optional[AwareDatetime] = Query(None),
        expiration_date_gte: Optional[AwareDatetime] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        order_by: Optional[list[str]] = Query(["created_at,1"]),
        container: Bootstrap = Depends(get_container),
        auth_user=Depends(auth_closure),
) -> list[Subscription]:
    order_by = [(x.split(",")[0], int(x.split(",")[1])) for x in order_by]
    sby = SubscriptionSby(
        ids=set(ids) if ids else None,
        statuses=set(statuses) if statuses else None,
        auth_ids={auth_user.id},
        subscriber_ids=set(subscriber_ids) if subscriber_ids else None,
        expiration_date_lt=expiration_date_lt,
        expiration_date_lte=expiration_date_lte,
        expiration_date_gt=expiration_date_gt,
        expiration_date_gte=expiration_date_gte,
        skip=skip,
        limit=limit,
        order_by=order_by,
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
    # todo вернуть permission service
    async with container.unit_of_work_factory().create_uow() as uow:
        result = await SubscriptionService(container.eventbus(), uow).get_one_by_id(sub_id)
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
        ids: Optional[set[SubId]] = Query(None),
        statuses: Optional[set[SubscriptionStatus]] = Query(None),
        subscriber_ids: Optional[set[str]] = Query(None),
        expiration_date_lt: Optional[AwareDatetime] = Query(None),
        expiration_date_lte: Optional[AwareDatetime] = Query(None),
        expiration_date_gt: Optional[AwareDatetime] = Query(None),
        expiration_date_gte: Optional[AwareDatetime] = Query(None),
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    sby = SubscriptionSby(
        ids=set(ids) if ids else None,
        statuses=set(statuses) if statuses else None,
        auth_ids={auth_user.id},
        subscriber_ids=set(subscriber_ids) if subscriber_ids else None,
        expiration_date_lt=expiration_date_lt,
        expiration_date_lte=expiration_date_lte,
        expiration_date_gt=expiration_date_gt,
        expiration_date_gte=expiration_date_gte,
    )
    # todo permission service
    async with container.unit_of_work_factory().create_uow() as uow:
        sby.auth_ids = {auth_user.id}
        service = SubscriptionService(container.eventbus(), uow)
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
