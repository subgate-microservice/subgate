from uuid import uuid4

import pytest

from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.subscription_api import SubscriptionCreate, SubscriptionUpdate
from backend.subscription.domain.cycle import Cycle, Period
from backend.subscription.domain.plan import Plan, Usage, UsageRate
from backend.subscription.domain.subscription import Subscription, SubscriptionStatus
from tests.conftest import current_user, get_async_client


async def create_plan(auth_user: AuthUser, usage_rates:list[UsageRate] = None):
    if not usage_rates:
        usage_rates = []
    async with get_container().unit_of_work_factory().create_uow() as uow:
        plan = Plan(
            title="Business",
            price=100,
            currency="USD",
            billing_cycle=Cycle.from_code(Period.Annual),
            level=3,
            auth_id=auth_user.id,
            usage_rates=usage_rates,
        )
        await uow.plan_repo().add_one(plan)
        await uow.commit()
        return plan


async def create_subscription(
        auth_user: AuthUser,
        usages: list[Usage] = None,
) -> Subscription:
    if not usages:
        usages = []
    rates = [UsageRate.from_usage(usage) for usage in usages]
    plan = await create_plan(auth_user, usage_rates=rates)
    sub = Subscription(
        id=uuid4(),
        auth_id=plan.auth_id,
        subscriber_id=str(uuid4()),
        plan=plan,
        status=SubscriptionStatus.Active,
        usages=usages,
        last_billing=get_current_datetime(),
        created_at=get_current_datetime(),
        updated_at=get_current_datetime(),
        paused_from=None,
        autorenew=False,
    )
    async with get_container().unit_of_work_factory().create_uow() as uow:
        await uow.subscription_repo().add_one(sub)
        await uow.commit()
        return sub


@pytest.mark.asyncio
async def test_create_one(current_user):
    user, token, expected_status_code = current_user
    plan = await create_plan(user)
    data = SubscriptionCreate(
        plan=plan,
        subscriber_id="AnySubscriberId",
        status=SubscriptionStatus.Active,
        usages=[],
        paused_from=None,
        autorenew=False,
    )
    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/subscription", json=data.model_dump(mode="json"), headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_get_by_id(current_user):
    user, token, expected_status_code = current_user
    data = await create_subscription(user)

    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/subscription/{data.id}", headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_delete_by_id(current_user):
    user, token, expected_status_code = current_user
    data = await create_subscription(user)

    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.delete(f"/subscription/{data.id}", headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_update_one(current_user):
    user, token, expected_status_code = current_user
    data = await create_subscription(user)

    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        update = SubscriptionUpdate.from_subscription(data)
        payload = update.model_dump(mode="json", exclude={"auth_ud"})
        response = await client.put(f"/subscription/{data.id}", json=payload, headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_get_selected(current_user):
    user, token, expected_status_code = current_user
    _data = [await create_subscription(user) for _ in range(1, 11)]

    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/subscription", headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_increase_usage(current_user):
    user, token, expected_status_code = current_user
    usages = [
        Usage(
            title="AnyTitle",code="first", unit="GB", available_units=100, used_units=0,
            renew_cycle=Cycle.from_code(Period.Monthly))
    ]
    sub = await create_subscription(user, usages=usages)

    async with get_async_client() as client:
        payload = {"code": "first", "value": 11}
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.patch(f"/subscription/{sub.id}/increase-usage", headers=headers, params=payload)
        assert response.status_code == expected_status_code


class TestGetSelected:
    @pytest.mark.asyncio
    async def test_get_selected_by_ids(self, current_user):
        # Before
        user, token, expected_status_code = current_user
        subs = [await create_subscription(user) for _ in range(0, 11)]

        # Test
        expected = subs[3:7]
        ids = [x.id for x in expected]

        async with get_async_client() as client:
            params = {"ids": [str(x) for x in ids]}
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"/subscription", headers=headers, params=params)
            assert response.status_code == expected_status_code

            real = []
            for data in response.json():
                data["auth_id"] = user.id
                data["plan"]["auth_id"] = user.id
                real.append(Subscription(**data))
            assert len(real) == len(ids)
            assert len(set(x.id for x in real).difference(ids)) == 0
