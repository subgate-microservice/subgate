from datetime import timedelta
from uuid import uuid4

import pytest

from backend.shared.exceptions import ItemAlreadyExist, ValidationError
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan, Cycle, UsageOld, UsageRateOld
from backend.subscription.domain.subscription import Subscription, SubscriptionStatus


@pytest.fixture()
def plan():
    plan = Plan(
        title="Business",
        price=100,
        currency="USD",
        billing_cycle=Cycle.from_code(Period.Annual),
        level=3,
        auth_id=uuid4(),
    )
    yield plan


def test_resume_paused_subscription(plan):
    sub = Subscription(
        subscriber_id="AnyID",
        plan=plan,
        last_billing=get_current_datetime() - timedelta(365),
        created_at=get_current_datetime() - timedelta(500),
        paused_from=get_current_datetime() - timedelta(10),
        auth_id=plan.auth_id,
        status=SubscriptionStatus.Paused,
    )
    assert sub.days_left == 10
    sub = sub.resume()
    assert sub.days_left == 10
    assert sub.status == SubscriptionStatus.Active
    assert sub.paused_from is None


def test_resume_active_subscription(plan):
    sub = Subscription(
        subscriber_id="AnyID",
        plan=plan,
        last_billing=get_current_datetime() - timedelta(360),
        created_at=get_current_datetime() - timedelta(500),
        auth_id=plan.auth_id,
    )
    assert sub.days_left == 5
    sub = sub.resume()
    assert sub.days_left == 5
    assert sub.status == SubscriptionStatus.Active
    assert sub.paused_from is None


def test_subscription_when_days_left_less_than_zero(plan):
    sub = Subscription(
        subscriber_id="AnyID",
        plan=plan,
        last_billing=get_current_datetime() - timedelta(400),
        created_at=get_current_datetime() - timedelta(500),
        auth_id=plan.auth_id,
    )
    assert sub.days_left == 0


class TestValidation:
    def test_status_validation(self, plan):
        with pytest.raises(ValueError):
            _ = Subscription(
                id=uuid4(),
                auth_id=uuid4(),
                subscriber_id="AnyId",
                plan=plan,
                status=SubscriptionStatus.Paused,
                expiration_date=get_current_datetime() + timedelta(33),
                paused_from=None,
                autorenew=False,
            )

    def test_paused_from_validation(self, plan):
        with pytest.raises(ValueError):
            _ = Subscription(
                id=uuid4(),
                auth_id=uuid4(),
                subscriber_id="AnyId",
                plan=plan,
                status=SubscriptionStatus.Active,
                paused_from=get_current_datetime(),
                autorenew=False,
            )

    def test_usages_validation_with_already_exist_usages(self, plan):
        usages = [
            UsageOld(
                title="AnyTitle",
                code="first",
                unit="GB",
                available_units=100,
                used_units=1,
                renew_cycle=Cycle.from_code(Period.Monthly),
            ),
            UsageOld(
                title="AnyTitle",
                code="first",
                unit="GB",
                available_units=100,
                used_units=1,
                renew_cycle=Cycle.from_code(Period.Monthly),
            ),
        ]

        with pytest.raises(ItemAlreadyExist):
            _ = Subscription(
                id=uuid4(),
                auth_id=uuid4(),
                subscriber_id="AnyId",
                plan=plan,
                status=SubscriptionStatus.Active,
                paused_from=None,
                autorenew=False,
                usages=usages
            )

    def test_subscription_with_extra_usages(self):
        inner_plan = Plan(
            title="Without usages",
            price=100,
            currency="USD",
            billing_cycle=Cycle.from_code(Period.Monthly),
            auth_id=uuid4(),
        )
        usages = [
            UsageOld(
                title="Extra",
                code="first",
                unit="GB",
                available_units=100,
                used_units=1,
                renew_cycle=Cycle.from_code(Period.Monthly),
            ),
        ]
        with pytest.raises(ValidationError):
            _subscription = Subscription(
                subscriber_id="AnyID",
                plan=inner_plan,
                usages=usages,
                auth_id=inner_plan.auth_id,
            )

    def test_subscription_with_extra_usage_rates(self):
        rates = [
            UsageRateOld(
                title="Extra",
                code="first",
                unit="GB",
                available_units=100,
                renew_cycle=Cycle.from_code(Period.Monthly),
            ),
        ]
        inner_plan = Plan(
            title="Without usages",
            price=100,
            currency="USD",
            billing_cycle=Cycle.from_code(Period.Monthly),
            auth_id=uuid4(),
            usage_rates=rates,
        )
        with pytest.raises(ValidationError):
            _subscription = Subscription(
                subscriber_id="AnyID",
                plan=inner_plan,
                auth_id=inner_plan.auth_id,
            )
