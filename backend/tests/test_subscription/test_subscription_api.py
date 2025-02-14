import pytest

from backend.subscription.adapters.schemas import SubscriptionCreate
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import Subscription
from tests.conftest import current_user, get_async_client


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_simple_subscription(self, current_user):
        user, token, expected_status_code = current_user
        headers = {"Authorization": f"Bearer {token}"}

        async with get_async_client() as client:
            plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
            subscription = Subscription.from_plan(plan, "AnyID")
            payload = SubscriptionCreate.from_subscription(subscription).model_dump(mode="json")

            response = await client.post(f"/subscription/", json=payload, headers=headers)
            assert response.status_code == expected_status_code
