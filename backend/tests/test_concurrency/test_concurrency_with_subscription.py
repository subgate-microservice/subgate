import asyncio

import pytest

from backend.bootstrap import get_container
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import UsageOld, Plan
from backend.subscription.domain.subscription import Subscription
from tests.conftest import current_user, get_async_client

container = get_container()


@pytest.mark.asyncio
async def test_increase_usage_with_concurrency(current_user):
    # Before
    user, token, expected_status_code = current_user
    usages = [
        UsageOld(
            title="AnyTitle", code="first", unit="GB", available_units=100, used_units=0,
            renew_cycle=Period.Monthly)
    ]
    plan = Plan("Business", 111, "USD", user.id)
    sub = Subscription.from_plan(plan, "SubID")
    for usage in usages:
        sub.usages.add(usage)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()

    async def increase_usage_task():
        payload = {"code": "first", "value": 20}
        headers = {"Authorization": f"Bearer {token}"}
        async with get_async_client() as client:
            response = await client.patch(f"/subscription/{sub.id}/increase-usage", headers=headers, params=payload)
            assert response.status_code == expected_status_code

    max_tasks = 6
    async with asyncio.TaskGroup() as tg:
        for _ in range(0, max_tasks):
            tg.create_task(increase_usage_task())

    async with container.unit_of_work_factory().create_uow() as uow:
        sub = await uow.subscription_repo().get_one_by_id(sub.id)
        assert sub.usages.get("first").used_units == max_tasks * 20
