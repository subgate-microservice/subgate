import datetime
from datetime import timedelta

import pytest

from backend.bootstrap import get_container
from backend.shared.exceptions import ValidationError
from backend.subscription.adapters.plan_api import PlanCreate, PlanUpdate
from backend.subscription.domain.cycle import Cycle, Period
from tests.conftest import current_user, get_async_client
from tests.fake_data import create_plan

container = get_container()


@pytest.mark.asyncio
async def test_create_one(current_user):
    user, token, expected_status_code = current_user
    plan_create = PlanCreate(
        title="Business",
        price=111,
        currency="USD",
        billing_cycle=Cycle.from_code(Period.Monthly),
    )
    async with get_async_client() as client:
        data = plan_create.model_dump(mode="json")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/plan", json=data, headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_get_one_by_id(current_user):
    user, token, expected_status_code = current_user

    async with get_container().unit_of_work_factory().create_uow() as uow:
        plans = []
        for i in range(11):
            plan = create_plan(user)
            plans.append(plan)
            await uow.plan_repo().add_one(plan)
        await uow.commit()

    # Test
    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/plan/{plans[4].id}", headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_get_selected(current_user):
    user, token, expected_status_code = current_user

    async with container.unit_of_work_factory().create_uow() as uow:
        plans = []
        for i in range(11):
            plan = create_plan(user)
            plans.append(plan)
            await uow.plan_repo().add_one(plan)

    # Test
    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/plan", headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_update_one(current_user):
    user, token, expected_status_code = current_user
    old_plan = create_plan(user)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(old_plan)
        await uow.commit()

    # Test
    async with get_async_client() as client:
        updated_plan = PlanUpdate.from_plan(old_plan).model_copy(update={"price": 34_000})
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.put(f"/plan/{updated_plan.id}", json=updated_plan.model_dump(mode="json"),
                                    headers=headers)
        assert response.status_code == expected_status_code


@pytest.mark.asyncio
async def test_delete_one(current_user):
    user, token, expected_status_code = current_user
    plan = create_plan(user)
    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.plan_repo().add_one(plan)
        await uow.commit()

    # Test
    async with get_async_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.delete(f"/plan/{plan.id}", headers=headers)
        assert response.status_code == expected_status_code


class TestUpdatePlanWithErrors:
    @pytest.mark.asyncio
    async def test_update_plan_with_updated_date_earlier_than_created_date(self, current_user):
        # Before
        user, token, expected_status_code = current_user
        plan = create_plan(user)
        async with container.unit_of_work_factory().create_uow() as uow:
            await uow.plan_repo().add_one(plan)
            await uow.commit()

        # Test
        async with get_async_client() as client:
            headers = {"Authorization": f"Bearer {token}"}
            payload = PlanUpdate(**plan.model_dump()).model_dump(mode="json")
            payload["updated_at"] = (
                    datetime.datetime.fromisoformat(payload.pop("updated_at")) - timedelta(days=111)
            ).isoformat()
            response = await client.put(f"/plan/{plan.id}", json=payload, headers=headers)
            assert response.status_code == 422

            data = response.json()
            assert len(data) == 1
            data = data.pop()
            assert data["exception_code"] == "validation_error"
            error = ValidationError.from_json(data)
            assert error.field == "updated_at"
            assert error.value == payload["updated_at"]
            assert error.message == "updated_at earlier than created_at"
