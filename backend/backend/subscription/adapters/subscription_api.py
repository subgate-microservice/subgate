from typing import Optional

from fastapi import Depends, APIRouter, Query
from pydantic import AwareDatetime

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import Bootstrap, get_container, auth_closure
from backend.subscription.adapters.schemas import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionRetrieve,
    UsageSchema, PlanInfoSchema, DiscountSchema)
from backend.subscription.application import subscription_service as services
from backend.subscription.domain.events import SubId
from backend.subscription.domain.subscription import (
    SubscriptionStatus, )
from backend.subscription.domain.subscription_repo import SubscriptionSby

subscription_router = APIRouter(
    prefix="/subscription",
    tags=["Subscription"],
)


@subscription_router.post("/")
async def create_subscription(
        subscription_create: SubscriptionCreate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    # todo вернуть permission service
    async with container.unit_of_work_factory().create_uow() as uow:
        subscription = subscription_create.to_subscription(auth_user.id)
        await services.create_subscription(subscription, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


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
) -> list[SubscriptionRetrieve]:
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
        subs = await uow.subscription_repo().get_selected(sby)
        schemas = [SubscriptionRetrieve.from_subscription(x) for x in subs]
    return schemas


@subscription_router.get("/{sub_id}")
async def get_subscription_by_id(
        sub_id: SubId,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> SubscriptionRetrieve:
    # todo вернуть permission service
    async with container.unit_of_work_factory().create_uow() as uow:
        sub = await uow.subscription_repo().get_one_by_id(sub_id)
        schema = SubscriptionRetrieve.from_subscription(sub)
    return schema


@subscription_router.get("/active-one/{subscriber_id}")
async def get_active_one(
        subscriber_id: str,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> Optional[SubscriptionRetrieve]:
    async with container.unit_of_work_factory().create_uow() as uow:
        sub = await uow.subscription_repo().get_subscriber_active_one(subscriber_id, auth_user.id)
        schema = SubscriptionRetrieve.from_subscription(sub)
    return schema


@subscription_router.delete("/{sub_id}")
async def delete_one_by_id(
        sub_id: SubId,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        target = await uow.subscription_repo().get_one_by_id(sub_id)
        await services.delete_subscription(target, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
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
        targets = await uow.subscription_repo().get_selected(sby)
        for target in targets:
            await services.delete_subscription(target, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.put("/{sub_id}")
async def update_subscription(
        subscription_update: SubscriptionUpdate,
        auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    # todo permission service
    async with container.unit_of_work_factory().create_uow() as uow:
        old_version = await uow.subscription_repo().get_one_by_id(subscription_update.id)
        new_version = subscription_update.to_subscription(auth_user.id, old_version.created_at)
        await services.update_subscription_from_another(old_version, new_version, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/increase-usage")
async def increase_usage(
        sub_id: SubId,
        code: str,
        value: float,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target = await uow.subscription_repo().get_one_by_id(sub_id)
        target.usages.get(code).increase(value)
        await services.save_updated_subscription(target, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/add-usages")
async def add_usages(
        sub_id: SubId,
        usages: list[UsageSchema],
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        for usage in usages:
            target_sub.usages.add(usage.to_usage())
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/remove-usages")
async def remove_usages(
        sub_id: SubId,
        codes: list[str],
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        for code in codes:
            target_sub.usages.remove(code)
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/update-usages")
async def update_usages(
        sub_id: SubId,
        usages: list[UsageSchema],
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        for usage in usages:
            target_sub.usages.update(usage.to_usage())
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/update-plan")
async def update_plan(
        sub_id: SubId,
        plan_info_schema: PlanInfoSchema,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        target_sub.plan_info = plan_info_schema.to_plan_info()
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/pause")
async def pause_subscription(
        sub_id: SubId,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        target_sub.pause()
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/resume")
async def resume_subscription(
        sub_id: SubId,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        target_sub.resume()
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/renew")
async def renew_subscription(
        sub_id: SubId,
        from_date: AwareDatetime = None,
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        target_sub.renew(from_date)
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/add-discounts")
async def add_discounts(
        sub_id: SubId,
        discounts: list[DiscountSchema],
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
):
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        for disc in discounts:
            target_sub.discounts.add(disc.to_discount())
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/remove-discounts")
async def remove_discounts(
        sub_id: SubId,
        codes: list[str],
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        for code in codes:
            target_sub.discounts.remove(code)
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"


@subscription_router.patch("/{sub_id}/update-discounts")
async def update_discounts(
        sub_id: SubId,
        discounts: list[DiscountSchema],
        _auth_user: AuthUser = Depends(auth_closure),
        container: Bootstrap = Depends(get_container),
) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        target_sub = await uow.subscription_repo().get_one_by_id(sub_id)
        for disc in discounts:
            target_sub.discounts.update(disc.to_discount())
        await services.save_updated_subscription(target_sub, uow)
        await container.eventbus().publish_from_unit_of_work(uow)
        await uow.commit()
    return "Ok"
