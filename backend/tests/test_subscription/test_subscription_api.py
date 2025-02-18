import pytest

from backend.bootstrap import get_container
from backend.shared.event_driven.base_event import Event
from backend.shared.utils import get_current_datetime
from backend.subscription.adapters.schemas import SubscriptionCreate, SubscriptionUpdate, UsageSchema, DiscountSchema
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.subscription import (
    SubscriptionStatus, Subscription, )
from backend.subscription.domain.events import SubscriptionPaused, SubscriptionResumed, SubscriptionRenewed, \
    SubscriptionUsageAdded, SubscriptionUsageRemoved, SubscriptionUsageUpdated, SubscriptionDiscountAdded, \
    SubscriptionDiscountRemoved, SubscriptionDiscountUpdated, SubscriptionUpdated
from backend.subscription.domain.usage import Usage
from tests.conftest import current_user, get_async_client
from tests.fakes import (event_handler, simple_sub, paused_sub, expired_sub, sub_with_discounts, sub_with_usages,
                         sub_with_fields)

container = get_container()


async def request(method: str, url, headers, expected_status_code, json=None):
    async with get_async_client() as client:
        response = await client.request(method, url, json=json, headers=headers)
        assert response.status_code == expected_status_code


async def patch_request(url, headers, expected_status_code, json=None):
    await request("PATCH", url, headers, expected_status_code, json)


async def put_request(url, headers, expected_status_code, json=None):
    await request("PUT", url, headers, expected_status_code, json)


async def full_update_sub_request(subscription: Subscription, headers: dict, expected_status_code):
    payload = SubscriptionUpdate.from_subscription(subscription).model_dump(mode="json")
    await request("PUT", f"/subscription/{subscription.id}", headers, expected_status_code, payload)


def get_headers(current_user):
    user, token, _ = current_user
    return {"Authorization": f"Bearer {token}"}


def check_event(event_handler, expected_event: Event):
    event_type = type(expected_event)
    real = event_handler.get(event_type)
    assert real is not None

    def mapper(key, value):
        if key == "changed_fields":
            return set(value)
        if key == "paused_from":
            return value.replace(second=0, microsecond=0)

    expected = {k: mapper(k, v) for k, v in expected_event.model_dump().items()}
    real = {k: mapper(k, v) for k, v in real.model_dump().items()}
    assert expected == real


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_simple_subscription(self, current_user):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        async with get_async_client() as client:
            plan = Plan("Simple", 100, "USD", user.id, Period.Monthly)
            subscription = Subscription.from_plan(plan, "AnyID")
            payload = SubscriptionCreate.from_subscription(subscription).model_dump(mode="json")

            response = await client.post(f"/subscription/", json=payload, headers=headers)
            assert response.status_code == expected_status_code


class TestStatusManagement:
    @pytest.mark.asyncio
    async def test_pause_subscription(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.pause()
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            expected_sub_updated = SubscriptionUpdated(
                subscription_id=simple_sub.id, changed_fields={"paused_from", "status"}, auth_id=simple_sub.auth_id,
            )
            expected_sub_paused = SubscriptionPaused(
                subscription_id=simple_sub.id, paused_from=get_current_datetime(), auth_id=simple_sub.auth_id,
            )
            assert len(event_handler.events) == 2
            check_event(event_handler, expected_sub_updated)
            check_event(event_handler, expected_sub_paused)

    @pytest.mark.asyncio
    async def test_resume_subscription(self, current_user, paused_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        paused_sub.resume()
        await full_update_sub_request(paused_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_resumed, sub_updated = event_handler.get(SubscriptionResumed), event_handler.get(SubscriptionUpdated)
            assert sub_resumed is not None
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"paused_from", "status"}

    @pytest.mark.asyncio
    async def test_renew_paused_subscription(self, current_user, paused_sub, event_handler):
        # Important!
        # Renew paused subscription is the same that resume paused subscription

        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        paused_sub._status = SubscriptionStatus.Active
        paused_sub._paused_from = None
        paused_sub.billing_info.last_billing = get_current_datetime()
        await full_update_sub_request(paused_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_resumed, sub_updated = event_handler.get(SubscriptionResumed), event_handler.get(SubscriptionUpdated)
            assert sub_resumed is not None
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"paused_from", "status"}

    @pytest.mark.asyncio
    async def test_renew_expired_subscription(self, current_user, expired_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        expired_sub.renew()
        await full_update_sub_request(expired_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_renewed, sub_updated = event_handler.get(SubscriptionRenewed), event_handler.get(SubscriptionUpdated)
            assert sub_renewed is not None
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"status", "billing_info.last_billing"}


class TestUsageManagement:
    @pytest.mark.asyncio
    async def test_add_usage(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.usages.add(
            Usage("First", "first", "GB", 100, Period.Monthly)
        )
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated, usage_added = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageAdded)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"usages.first:added"}
            assert usage_added is not None
            assert usage_added.code == "first"

    @pytest.mark.asyncio
    async def test_update_usage(self, current_user, sub_with_usages, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        sub_with_usages.usages.get("first").increase(150)
        await full_update_sub_request(sub_with_usages, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated, u_updated = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"usages.first:updated"}
            assert u_updated is not None
            assert u_updated.code == "first"
            assert u_updated.used_units == 150

    @pytest.mark.asyncio
    async def test_remove_usage(self, current_user, sub_with_usages, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        sub_with_usages.usages.remove("first")
        await full_update_sub_request(sub_with_usages, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated, u_removed = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageRemoved)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"usages.first:removed"}
            assert u_removed is not None
            assert u_removed.code == "first"


class TestDiscountManagement:
    @pytest.mark.asyncio
    async def test_add_discount(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.discounts.add(
            Discount(title="Second", code="second", size=0.5, description="Hello world",
                     valid_until=get_current_datetime())
        )
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated, d_added = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionDiscountAdded)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"discounts.second:added"}
            assert d_added is not None
            assert d_added.code == "second"

    @pytest.mark.asyncio
    async def test_remove_discount(self, current_user, sub_with_discounts, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        sub_with_discounts.discounts.remove("first")
        await full_update_sub_request(sub_with_discounts, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated, d_removed = event_handler.get(SubscriptionUpdated), event_handler.get(
                SubscriptionDiscountRemoved)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"discounts.first:removed"}
            assert d_removed is not None
            assert d_removed.code == "first"

    @pytest.mark.asyncio
    async def test_update_discount(self, current_user, sub_with_discounts, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        sub_with_discounts.discounts.get("first").title = "Hello world!"
        await full_update_sub_request(sub_with_discounts, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated, d_updated = event_handler.get(SubscriptionUpdated), event_handler.get(
                SubscriptionDiscountUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"discounts.first:updated"}
            assert d_updated is not None
            assert d_updated.title == "Hello world!"


class TestOtherFieldsManagement:
    @pytest.mark.asyncio
    async def test_update_plan_info(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.plan_info.title = "Updated title"
        simple_sub.plan_info.level = 755
        simple_sub.plan_info.features = "Updated features"
        simple_sub.plan_info.description = "Updated description"
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"plan_info.title", "plan_info.level", "plan_info.features",
                                                       "plan_info.description", }

    @pytest.mark.asyncio
    async def test_update_billing_info(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.billing_info.price = 99
        simple_sub.billing_info.currency = "EUR"
        simple_sub.billing_info.billing_cycle = Period.Semiannual
        simple_sub.billing_info.last_billing = get_current_datetime().replace(year=1999)
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"billing_info.price", "billing_info.currency",
                                                       "billing_info.billing_cycle", "billing_info.last_billing", }

    @pytest.mark.asyncio
    async def test_update_fields(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.fields = {"Hello": 1, "World": 2}
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"fields", }

    @pytest.mark.asyncio
    async def test_update_fields_inner_values(self, current_user, sub_with_fields, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        sub_with_fields.fields["any_value"] = "Updated"
        await full_update_sub_request(sub_with_fields, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"fields", }

    @pytest.mark.asyncio
    async def test_update_autorenew(self, current_user, sub_with_fields, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        async with get_async_client() as client:
            sub_with_fields.autorenew = True
            payload = SubscriptionUpdate.from_subscription(sub_with_fields).model_dump(mode="json")
            response = await client.put(f"/subscription/{sub_with_fields.id}", json=payload, headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"autorenew"}

    @pytest.mark.asyncio
    async def test_update_subscriber_id(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        simple_sub.subscriber_id = "UpdatedID"
        await full_update_sub_request(simple_sub, headers, expected_status_code)

        # Check events
        if expected_status_code < 400:
            sub_updated = event_handler.get(SubscriptionUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"subscriber_id"}


class TestSpecificStatusAPI:
    @pytest.mark.asyncio
    async def test_pause_endpoint(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        async with get_async_client() as client:
            response = await client.patch(f"/subscription/{simple_sub.id}/pause", headers=headers)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            assert len(event_handler.events) == 2
            sub_updated, sub_paused = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionPaused)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"status", "paused_from"}


class TestSpecificUsageAPI:
    @pytest.mark.asyncio
    async def test_add_usages_endpoint(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        usages = [Usage("First", "first", "GB", 111, Period.Monthly)]

        async with get_async_client() as client:
            payload = [UsageSchema.from_usage(x).model_dump(mode="json") for x in usages]
            response = await client.patch(f"/subscription/{simple_sub.id}/add-usages", headers=headers, json=payload)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            assert len(event_handler.events) == 2
            sub_updated, u_added = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageAdded)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {"usages.first:added"}

    @pytest.mark.asyncio
    async def test_update_usages_endpoint(self, current_user, sub_with_usages, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        updated = next(x for x in sub_with_usages.usages)
        updated.increase(150)

        async with get_async_client() as client:
            payload = [UsageSchema.from_usage(updated).model_dump(mode="json")]
            response = await client.patch(f"/subscription/{sub_with_usages.id}/update-usages", headers=headers,
                                          json=payload)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            assert len(event_handler.events) == 2
            sub_updated, u_updated = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageUpdated)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {f"usages.{updated.code}:updated"}

    @pytest.mark.asyncio
    async def test_remove_usages_endpoint(self, current_user, sub_with_usages, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        remove_code = next(x for x in sub_with_usages.usages).code

        async with get_async_client() as client:
            payload = [remove_code]
            response = await client.patch(f"/subscription/{sub_with_usages.id}/remove-usages", headers=headers,
                                          json=payload)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            assert len(event_handler.events) == 2
            sub_updated, u_removed = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionUsageRemoved)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {f"usages.{remove_code}:removed"}


class TestSpecificDiscountAPI:
    @pytest.mark.asyncio
    async def test_add_discounts_endpoint(self, current_user, simple_sub, event_handler):
        user, token, expected_status_code = current_user
        headers = get_headers(current_user)

        discounts = [Discount("First", "first", "Hello", 0.5, get_current_datetime())]

        async with get_async_client() as client:
            payload = [DiscountSchema.from_discount(x).model_dump(mode="json") for x in discounts]
            response = await client.patch(f"/subscription/{simple_sub.id}/add-discounts", headers=headers,
                                          json=payload)
            assert response.status_code == expected_status_code

        # Check events
        if response.status_code < 400:
            assert len(event_handler.events) == 2
            sub_updated, d_added = event_handler.get(SubscriptionUpdated), event_handler.get(SubscriptionDiscountAdded)
            assert sub_updated is not None
            assert set(sub_updated.changed_fields) == {f"discounts.{discounts[0].code}:added"}

    @pytest.mark.asyncio
    async def test_remove_discounts_endpoint(self, current_user, sub_with_discounts, event_handler):
        user, token, expected_status_code = current_user
        sub_id = sub_with_discounts.id
        headers = get_headers(current_user)

        payload = ["first"]
        await patch_request(f"/subscription/{sub_id}/remove-discounts", headers, expected_status_code, json=payload)

        if expected_status_code < 400:
            assert len(event_handler.events) == 2
            removed = SubscriptionDiscountRemoved(subscription_id=sub_id, code="first", auth_id=user.id)
            updated = SubscriptionUpdated(
                subscription_id=sub_id, changed_fields={"discounts.first:removed"}, auth_id=user.id,
            )
            check_event(event_handler, removed)
            check_event(event_handler, updated)

    @pytest.mark.asyncio
    async def test_update_discounts_endpoint(self, current_user, sub_with_discounts, event_handler):
        user, token, expected_status_code = current_user
        sub_id = sub_with_discounts.id
        headers = get_headers(current_user)

        target = sub_with_discounts.discounts.get("first")
        target.title = "UPDATED"
        payload = [DiscountSchema.from_discount(target).model_dump(mode="json")]
        await patch_request(f"subscription/{sub_id}/update-discounts", headers, expected_status_code, payload)

        if expected_status_code < 400:
            assert len(event_handler.events) == 2
            updated = SubscriptionUpdated(
                subscription_id=sub_id, changed_fields={"discounts.first:updated"}, auth_id=user.id,
            )
            discount_updated = SubscriptionDiscountUpdated(
                subscription_id=sub_id, title="UPDATED", code="first", size=target.size, valid_until=target.valid_until,
                description=target.description, auth_id=user.id)
            check_event(event_handler, updated)
            check_event(event_handler, discount_updated)
