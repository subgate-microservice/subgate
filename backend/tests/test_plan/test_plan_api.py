import pytest
import pytest_asyncio

from backend.bootstrap import get_container
from backend.subscription.adapters.plan_api import PlanCreate, PlanUpdate
from backend.subscription.domain.cycle import Cycle, Period
from backend.subscription.domain.plan import Plan
from tests.conftest import current_user, get_async_client
from tests.fake_data import create_plan

container = get_container()


class TestCreate:
    @pytest.mark.asycnio
    async def test_create_simple_plan(self, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
            payload = PlanCreate.from_plan(plan).model_dump(mode="json")
            response = await client.post(f"/plan/", json=payload, headers=headers)
            assert response.status_code == expected_status_code


class TestGet:
    @pytest_asyncio.fixture()
    async def simple_plan(self, current_user):
        user, token, expected_status_code = current_user
        plan = Plan.create("Simple", 100, "USD", user.id, Period.Monthly)
        async with container.unit_of_work_factory().create_uow() as uow:
            await uow.plan_repo().add_one(plan)
            await uow.commit()
        yield plan

    @pytest.mark.asyncio
    async def test_get_one_by_id(self, simple_plan, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            response = await client.get(f"/plan/{simple_plan.id}", headers=headers)
            assert response.status_code == expected_status_code


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
