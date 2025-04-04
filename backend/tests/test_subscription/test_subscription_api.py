from datetime import timedelta

import pytest

from backend.bootstrap import get_container
from backend.shared.utils.dt import get_current_datetime
from backend.subscription.adapters.schemas import SubscriptionCreate, SubscriptionUpdate, UsageSchema, DiscountSchema
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.enums import SubscriptionStatus
from backend.subscription.domain.events import (
    SubPaused, SubResumed, SubRenewed,
    SubUsageAdded, SubUsageRemoved, SubUsageUpdated, SubDiscountAdded,
    SubDiscountRemoved, SubDiscountUpdated, SubUpdated, SubExpired, SubCreated)
from backend.subscription.domain.subscription import (
    Subscription, )
from backend.subscription.domain.usage import Usage
from tests.conftest import client
from tests.fakes import (event_handler, simple_sub, paused_sub, expired_sub, sub_with_discounts, sub_with_usages,
                         sub_with_fields, simple_plan)
from tests.helpers import check_changes

container = get_container()


async def full_update(subscription: Subscription, client_):
    payload = SubscriptionUpdate.from_subscription(subscription).model_dump(mode="json")
    await client_.put(f"/subscription/{subscription.id}", json=payload)


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_simple_subscription(self, client, event_handler, simple_plan):
        subscription = Subscription.from_plan(simple_plan, "AnyID")
        payload = SubscriptionCreate.from_subscription(subscription).model_dump(mode="json")
        await client.post(f"/subscription/", json=payload)

        assert len(event_handler.events) == 1

    @pytest.mark.asyncio
    async def test_create_second_subscription_when_another_one_exist(self, client, event_handler, simple_plan):
        # First
        sub1 = Subscription.from_plan(simple_plan, "AnyID")
        payload1 = SubscriptionCreate.from_subscription(sub1).model_dump(mode="json")
        await client.post(f"/subscription/", json=payload1)
        sub_created = event_handler.get(SubCreated)
        assert sub_created.status == SubscriptionStatus.Active

        # Second
        sub2 = Subscription.from_plan(simple_plan, "AnyID")
        payload2 = SubscriptionCreate.from_subscription(sub2).model_dump(mode="json")
        await client.post("/subscription", json=payload2)
        sub_created = event_handler.get(SubCreated)
        assert sub_created.status == SubscriptionStatus.Paused


class TestStatusManagement:
    @pytest.mark.asyncio
    async def test_pause_subscription(self, client, simple_sub, event_handler):
        simple_sub.pause()
        await full_update(simple_sub, client)

        # Check events
        assert len(event_handler.events) == 2
        s_paused, s_updated = event_handler.get(SubPaused), event_handler.get(SubUpdated)
        assert s_updated
        assert s_updated
        expected = {
            "paused_from": get_current_datetime(),
            "status": SubscriptionStatus.Paused,
            "updated_at": get_current_datetime(),
        }
        check_changes(s_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_resume_paused_subscription(self, client, paused_sub, event_handler):
        paused_sub.resume()
        await full_update(paused_sub, client)

        # Check events
        sub_resumed, sub_updated = event_handler.get(SubResumed), event_handler.get(SubUpdated)
        assert sub_resumed is not None
        assert sub_updated is not None
        expected = {
            "paused_from": None,
            "status": SubscriptionStatus.Active,
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_renew_paused_subscription(self, client, paused_sub, event_handler):
        renew_from = get_current_datetime() + timedelta(milliseconds=1)
        paused_sub.renew(renew_from)
        await full_update(paused_sub, client)

        # Check events
        sub_renewed, sub_updated = event_handler.get(SubRenewed), event_handler.get(SubUpdated)
        assert sub_renewed is not None
        assert sub_updated is not None
        expected = {
            "paused_from": None,
            "status": SubscriptionStatus.Active,
            "billing_info.last_billing": renew_from,
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_renew_expired_subscription(self, client, expired_sub, event_handler):
        expired_sub.renew()
        await full_update(expired_sub, client)

        # Check events
        sub_renewed, sub_updated = event_handler.get(SubRenewed), event_handler.get(SubUpdated)
        assert sub_renewed is not None
        assert sub_updated is not None
        expected = {
            "status": SubscriptionStatus.Active,
            "billing_info.last_billing": get_current_datetime(),
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_expire_subscription(self, client, simple_sub, event_handler):
        simple_sub.expire()
        await full_update(simple_sub, client)

        # Check events
        sub_expired, sub_updated = event_handler.get(SubExpired), event_handler.get(SubUpdated)
        assert sub_expired is not None
        assert sub_updated is not None
        expected = {
            "status": SubscriptionStatus.Expired,
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)


class TestUsageManagement:
    @pytest.mark.asyncio
    async def test_add_usage(self, client, simple_sub, event_handler):
        simple_sub.usages.add(
            Usage("First", "first", "GB", 100, Period.Monthly)
        )
        await full_update(simple_sub, client)

        # Check events
        sub_updated, usage_added = event_handler.get(SubUpdated), event_handler.get(SubUsageAdded)
        assert sub_updated is not None
        expected = {"usages.first": "action:added", "updated_at": get_current_datetime(), }
        check_changes(sub_updated.changes, expected)
        assert usage_added is not None
        assert usage_added.code == "first"

    @pytest.mark.asyncio
    async def test_update_usage(self, client, sub_with_usages, event_handler):
        sub_with_usages.usages.get("first").increase(150)
        await full_update(sub_with_usages, client)

        # Check events
        sub_updated, u_updated = event_handler.get(SubUpdated), event_handler.get(SubUsageUpdated)
        assert sub_updated is not None
        expected = {"usages.first": "action:updated", "updated_at": get_current_datetime(), }
        check_changes(sub_updated.changes, expected)
        assert u_updated is not None
        assert u_updated.code == "first"
        assert u_updated.changes == {"used_units": 150}
        assert u_updated.delta == 150

    @pytest.mark.asyncio
    async def test_remove_usage(self, client, sub_with_usages, event_handler):
        sub_with_usages.usages.remove("first")
        await full_update(sub_with_usages, client)

        # Check events
        sub_updated, u_removed = event_handler.get(SubUpdated), event_handler.get(SubUsageRemoved)
        assert sub_updated is not None
        expected = {"usages.first": "action:removed", "updated_at": get_current_datetime(), }
        check_changes(sub_updated.changes, expected)
        assert u_removed is not None
        assert u_removed.code == "first"


class TestDiscountManagement:
    @pytest.mark.asyncio
    async def test_add_discount(self, client, simple_sub, event_handler):
        simple_sub.discounts.add(
            Discount(title="Second", code="second", size=0.5, description="Hello world",
                     valid_until=get_current_datetime())
        )
        await full_update(simple_sub, client)

        # Check events
        sub_updated, d_added = event_handler.get(SubUpdated), event_handler.get(SubDiscountAdded)
        assert sub_updated is not None
        expected = {"discounts.second": "action:added", "updated_at": get_current_datetime(), }
        check_changes(sub_updated.changes, expected)
        assert d_added is not None
        assert d_added.code == "second"

    @pytest.mark.asyncio
    async def test_remove_discount(self, client, sub_with_discounts, event_handler):
        sub_with_discounts.discounts.remove("first")
        await full_update(sub_with_discounts, client)

        # Check events
        sub_updated, d_removed = event_handler.get(SubUpdated), event_handler.get(
            SubDiscountRemoved)
        assert sub_updated is not None
        expected = {"discounts.first": "action:removed", "updated_at": get_current_datetime(), }
        check_changes(sub_updated.changes, expected)
        assert d_removed is not None
        assert d_removed.code == "first"

    @pytest.mark.asyncio
    async def test_update_discount(self, client, sub_with_discounts, event_handler):
        sub_with_discounts.discounts.get("first").title = "Hello, World!"
        await full_update(sub_with_discounts, client)

        sub_updated, d_updated = event_handler.get(SubUpdated), event_handler.get(
            SubDiscountUpdated)
        assert sub_updated is not None
        expected = {"discounts.first": "action:updated", "updated_at": get_current_datetime(), }
        check_changes(sub_updated.changes, expected)
        assert d_updated is not None
        assert d_updated.changes == {"title": "Hello, World!"}


class TestOtherFieldsManagement:
    @pytest.mark.asyncio
    async def test_update_plan_info(self, client, simple_sub, event_handler):
        simple_sub.plan_info.title = "Updated title"
        simple_sub.plan_info.level = 755
        simple_sub.plan_info.features = "Updated features"
        simple_sub.plan_info.description = "Updated description"
        await full_update(simple_sub, client)

        # Check events
        sub_updated = event_handler.get(SubUpdated)
        assert sub_updated is not None
        expected = {
            "plan_info.title": "Updated title",
            "plan_info.level": 755,
            "plan_info.features": "Updated features",
            "plan_info.description": "Updated description",
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_billing_info(self, client, simple_sub, event_handler):
        simple_sub.billing_info.price = 99
        simple_sub.billing_info.currency = "EUR"
        simple_sub.billing_info.billing_cycle = Period.Semiannual
        simple_sub.billing_info.last_billing = get_current_datetime().replace(year=1999)
        await full_update(simple_sub, client)

        # Check events
        sub_updated = event_handler.get(SubUpdated)
        assert sub_updated is not None
        expected = {
            "billing_info.price": 99,
            "billing_info.currency": "EUR",
            "billing_info.billing_cycle": Period.Semiannual,
            "billing_info.last_billing": simple_sub.billing_info.last_billing,
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_fields(self, client, simple_sub, event_handler):
        simple_sub.fields = {"Hello": 1, "World": 2}
        await full_update(simple_sub, client)

        # Check events
        sub_updated = event_handler.get(SubUpdated)
        assert sub_updated is not None
        expected = {
            "fields": {"Hello": 1, "World": 2},
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_fields_inner_values(self, client, sub_with_fields, event_handler):
        sub_with_fields.fields["any_value"] = "Updated"
        await full_update(sub_with_fields, client)

        # Check events
        sub_updated = event_handler.get(SubUpdated)
        assert sub_updated is not None
        expected = {"fields": sub_with_fields.fields, "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_subscriber_id(self, client, simple_sub, event_handler):
        simple_sub.subscriber_id = "UpdatedID"
        await full_update(simple_sub, client)

        # Check events
        sub_updated = event_handler.get(SubUpdated)
        assert sub_updated is not None
        expected = {"subscriber_id": "UpdatedID", "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)


class TestSpecificStatusAPI:
    @pytest.mark.asyncio
    async def test_pause_endpoint(self, client, simple_sub, event_handler):
        response = await client.patch(f"/subscription/{simple_sub.id}/pause")
        response.raise_for_status()

        # Check events
        if response.status_code < 400:
            assert len(event_handler.events) == 2
            sub_updated, sub_paused = event_handler.get(SubUpdated), event_handler.get(SubPaused)
            assert sub_updated is not None
            expected = {
                "status": SubscriptionStatus.Paused,
                "paused_from": get_current_datetime(),
                "updated_at": get_current_datetime()
            }
            check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_resume_endpoint(self, client, paused_sub, event_handler):
        response = await client.patch(f"/subscription/{paused_sub.id}/resume")
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, sub_paused = event_handler.get(SubUpdated), event_handler.get(SubPaused)
        assert sub_updated is not None
        expected = {
            "status": SubscriptionStatus.Active,
            "paused_from": None,
            "updated_at": get_current_datetime(),
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_renew_active_endpoint(self, client, simple_sub, event_handler):
        from_date = get_current_datetime() + timedelta(days=3)
        params = {"from_date": from_date}
        response = await client.patch(f"/subscription/{simple_sub.id}/renew", params=params)
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, sub_paused = event_handler.get(SubUpdated), event_handler.get(SubPaused)
        assert sub_updated is not None
        expected = {
            "billing_info.last_billing": from_date,
            "updated_at": get_current_datetime()
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_renew_expired_endpoint(self, client, expired_sub, event_handler):
        from_date = get_current_datetime() + timedelta(days=3)
        params = {"from_date": from_date}
        response = await client.patch(f"/subscription/{expired_sub.id}/renew", params=params)
        response.raise_for_status()

        # Check events
        assert len(event_handler.events) == 2
        sub_updated, sub_paused = event_handler.get(SubUpdated), event_handler.get(SubPaused)
        assert sub_updated is not None
        expected = {
            "status": SubscriptionStatus.Active,
            "billing_info.last_billing": from_date,
            "updated_at": get_current_datetime()
        }
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_expire_endpoint(self, client, simple_sub, event_handler):
        response = await client.patch(f"/subscription/{simple_sub.id}/expire")
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, sub_paused = event_handler.get(SubUpdated), event_handler.get(SubPaused)
        assert sub_updated is not None
        expected = {"status": SubscriptionStatus.Expired, "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)


class TestSpecificUsageAPI:
    @pytest.mark.asyncio
    async def test_add_usages_endpoint(self, client, simple_sub, event_handler):
        usages = [Usage("First", "first", "GB", 111, Period.Monthly)]
        payload = [UsageSchema.from_usage(x).model_dump(mode="json") for x in usages]
        response = await client.patch(f"/subscription/{simple_sub.id}/add-usages", json=payload)
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, u_added = event_handler.get(SubUpdated), event_handler.get(SubUsageAdded)
        assert sub_updated is not None
        expected = {"usages.first": "action:added", "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_usages_endpoint(self, client, sub_with_usages, event_handler):
        updated = next(x for x in sub_with_usages.usages)
        updated.increase(150)

        payload = [UsageSchema.from_usage(updated).model_dump(mode="json")]
        response = await client.patch(f"/subscription/{sub_with_usages.id}/update-usages", json=payload)
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, u_updated = event_handler.get(SubUpdated), event_handler.get(SubUsageUpdated)
        assert sub_updated is not None
        expected = {f"usages.{updated.code}": "action:updated", "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_remove_usages_endpoint(self, client, sub_with_usages, event_handler):
        remove_code = next(x for x in sub_with_usages.usages).code
        payload = [remove_code]
        response = await client.patch(f"/subscription/{sub_with_usages.id}/remove-usages", json=payload)
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, u_removed = event_handler.get(SubUpdated), event_handler.get(SubUsageRemoved)

        assert sub_updated is not None
        expected = {f"usages.{remove_code}": "action:removed", "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)


class TestSpecificDiscountAPI:
    @pytest.mark.asyncio
    async def test_add_discounts_endpoint(self, client, simple_sub, event_handler):
        discounts = [Discount("First", "first", "Hello", 0.5, get_current_datetime())]
        payload = [DiscountSchema.from_discount(x).model_dump(mode="json") for x in discounts]
        response = await client.patch(f"/subscription/{simple_sub.id}/add-discounts", json=payload)
        response.raise_for_status()

        assert len(event_handler.events) == 2
        sub_updated, d_added = event_handler.get(SubUpdated), event_handler.get(SubDiscountAdded)

        assert sub_updated is not None
        expected = {f"discounts.{discounts[0].code}": "action:added", "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)

    @pytest.mark.asyncio
    async def test_remove_discounts_endpoint(self, client, sub_with_discounts, event_handler):
        payload = ["first"]
        await client.patch(f"/subscription/{sub_with_discounts.id}/remove-discounts", json=payload)

        assert len(event_handler.events) == 2
        removed, updated = event_handler.get(SubDiscountRemoved), event_handler.get(SubUpdated)
        assert removed.code == "first"

        expected = {"discounts.first": "action:removed", "updated_at": get_current_datetime()}
        check_changes(updated.changes, expected)

    @pytest.mark.asyncio
    async def test_update_discounts_endpoint(self, client, sub_with_discounts, event_handler):
        target = sub_with_discounts.discounts.get("first")
        target.title = "UPDATED"
        payload = [DiscountSchema.from_discount(target).model_dump(mode="json")]
        await client.patch(f"subscription/{sub_with_discounts.id}/update-discounts", json=payload)

        assert len(event_handler.events) == 2
        discount_updated = event_handler.get(SubDiscountUpdated)
        assert discount_updated.changes == {"title": "UPDATED"}

        sub_updated = event_handler.get(SubUpdated)
        expected = {"discounts.first": "action:updated", "updated_at": get_current_datetime()}
        check_changes(sub_updated.changes, expected)
