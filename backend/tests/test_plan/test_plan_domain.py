from uuid import uuid4

from backend.subscription.domain.cycle import Period
from backend.subscription.domain.plan import Plan
from backend.subscription.domain.usage import UsageRate


def test_to_plan_updated_event():
    auth_id = uuid4()
    old_plan = Plan.create("Personal", 100, "USD", auth_id)
    new_plan = Plan.create("Updated", 111, "EUR", auth_id)
    new_plan.usage_rates.add(UsageRate("first", "Hello", "GB", 100, Period.Monthly))
    event = old_plan.to_plan_updated(new_plan)
    print(event)
