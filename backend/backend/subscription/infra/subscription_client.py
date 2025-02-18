from operator import attrgetter
from typing import Optional

import aiohttp

from backend.subscription.domain.plan import Plan, PlanId
from backend.subscription.domain.subscription import Subscription, SubscriptionStatus
from backend.subscription.domain.events import SubId


class SubscriptionClient:
    def __init__(
            self,
            base_url: str,
            api_key: str,
    ):
        self._BASE_URL = base_url
        self._API_KEY = api_key
        self._headers = {
            "Authorization": f"Bearer {self._API_KEY}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs):
        try:
            url = f"{self._BASE_URL}/{endpoint}"
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.client_exceptions.ClientConnectorError:
            raise Exception(f"SubscriptionClient cannot connect to {self._BASE_URL}")

    async def create_plan(self, plan: Plan) -> None:
        data = plan.model_dump(mode="json")
        await self._request("POST", "plan", json=data)

    async def update_plan(self, plan: Plan) -> None:
        data = plan.model_dump(mode="json")
        await self._request("PUT", f"plan/{plan.id}", json=data)

    async def get_plan_by_id(self, plan_id: PlanId) -> Plan:
        response_data = await self._request("GET", f"plan/{plan_id}")
        return Plan(**response_data)

    async def get_selected_plans(
            self,
            ids: Optional[set[PlanId]] = None,
            order_by: list[tuple[str, int]] = None,
            skip: int = 0,
            limit: int = 100,
    ) -> list[Plan]:
        if not order_by:
            order_by = [("created_at", 1)]
        sby = dict(
            ids=[str(x) for x in ids],
            skip=skip,
            limit=limit,
            order_by=order_by,
        )
        response_data = await self._request("POST", f"plan/get-selected", json=sby)
        return [Plan(**x) for x in response_data]

    async def delete_plan(self, plan_id: PlanId) -> None:
        await self._request("DELETE", f"plan/{plan_id}")

    async def create_subscription(self, sub: Subscription) -> None:
        data = sub.model_dump(mode="json")
        await self._request("POST", "subscription", json=data)

    async def update_subscription(self, sub: Subscription) -> None:
        data = sub.model_dump(mode="json")
        await self._request("PUT", f"subscription/{sub.id}", json=data)

    async def get_selected_subscriptions(
            self,
            ids: Optional[set[SubId]] = None,
            statuses: Optional[set[SubscriptionStatus]] = None,
            expired: bool = False,
            order_by: list[tuple[str, int]] = None,
            skip: int = 0,
            limit: int = 100,
    ):
        if not order_by:
            order_by = [("created_at", 1)]
        sby = dict(
            ids=[str(x) for x in ids],
            statuses=statuses,
            expired=str(expired),
            skip=skip,
            limit=limit,
            order_by=order_by,
        )
        response_data = await self._request("POST", f"subscription/get-selected", json=sby)
        return [Subscription(**x) for x in response_data]

    async def get_subscription_by_id(self, sub_id: SubId) -> Subscription:
        response_data = await self._request("GET", f"subscription/{sub_id}")
        return Subscription(**response_data)

    async def get_user_active_subscription(self, user_id: str) -> Optional[Subscription]:
        response_data = await self._request("GET", f"subscription/active/{user_id}")
        if response_data:
            response_data = Subscription(**response_data)
        return response_data

    async def delete_subscription(self, sub_id: SubId) -> None:
        await self._request("DELETE", f"subscription/{sub_id}")


class FakeSubscriptionClient(SubscriptionClient):
    def __init__(self, data: dict[SubId, Subscription] = None):
        super().__init__("", "")
        self._data = {key: value.model_copy(deep=True) for key, value in data.items()} if data else {}

    async def create_subscription(self, sub: Subscription) -> None:
        self._data[sub.id] = sub.model_copy(deep=True)

    async def update_subscription(self, sub: Subscription) -> None:
        if not self._data.get(sub.id):
            raise LookupError
        self._data[sub.id] = sub.model_copy(deep=True)

    async def get_selected_subscriptions(
            self,
            ids: Optional[set[SubId]] = None,
            statuses: Optional[set[SubscriptionStatus]] = None,
            expired: bool = False,
            order_by: list[tuple[str, int]] = None,
            skip: int = 0,
            limit: int = 100,
    ):
        result = []
        for sub in self._data.values():
            if all([
                ids is None or sub.id in ids,
                statuses is None or sub.status in statuses,
                sub.days_left > 0 is not expired,
            ]):
                result.append(sub.model_copy(deep=True))

        # Если order_by передан, сортируем result
        if order_by:
            for field, direction in reversed(order_by):  # reversed для приоритетной сортировки
                result = sorted(
                    result,
                    key=attrgetter(field),
                    reverse=(direction == -1)  # -1 для убывания
                )

        return result[skip: skip + limit]

    async def get_subscription_by_id(self, sub_id: SubId) -> Subscription:
        try:
            return self._data[sub_id]
        except KeyError:
            raise LookupError

    async def get_user_active_subscription(self, target_id: str) -> Optional[Subscription]:
        result = [x for x in self._data.values() if x.subscriber_id == target_id]
        result = list(sorted(result, key=lambda x: x.plan.level, reverse=True))
        for sub in result:
            if sub.days_left:
                return sub

    async def delete_subscription(self, sub_id: SubId) -> None:
        self._data.pop(sub_id, None)
