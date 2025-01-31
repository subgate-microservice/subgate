from uuid import uuid4

from pydantic import AwareDatetime

from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.shared.events import EventCode
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Cycle
from backend.subscription.domain.plan import Plan, Usage
from backend.subscription.domain.subscription import SubscriptionStatus, Subscription
from backend.webhook.domain.telegram import Telegram
from backend.webhook.domain.webhook import Webhook


def create_plan(auth_user: AuthUser = None, title="Business", level=10):
    return Plan(
        title=title,
        price=100,
        currency="USD",
        billing_cycle=Cycle(title="Monthly", code="Monthly", cycle_in_days=31),
        level=level,
        auth_id=auth_user.id if auth_user else uuid4(),
    )


def create_subscription(
        plan: Plan = None,
        subscriber_id: str = None,
        usages: list[Usage] = None,
        auth_user: AuthUser = None,
        last_billing: AwareDatetime = None,
):
    auth_user = auth_user if auth_user else AuthUser()
    my_plan = create_plan(auth_user=auth_user) if not plan else plan
    subscriber_id = str(uuid4()) if not subscriber_id else subscriber_id
    usages = usages if usages else []
    last_billing = last_billing if last_billing else get_current_datetime()
    return Subscription(
        id=uuid4(),
        auth_id=auth_user.id,
        subscriber_id=subscriber_id,
        plan=my_plan,
        status=SubscriptionStatus.Active,
        usages=usages,
        paused_from=None,
        autorenew=False,
        last_billing=last_billing,
        created_at=last_billing,
    )


def create_webhook():
    return Webhook(
        event_code=EventCode.SubscriptionExpired,
        target_url="https://google.com",
        auth_id=uuid4(),
    )


def create_apikey(auth_user: AuthUser = None):
    if auth_user is None:
        auth_user = AuthUser(id=uuid4())
    return Apikey(
        title=f"Title_{uuid4()}",
        auth_user=auth_user,
    )


def create_telegraph_message(url: str, data: str = None) -> Telegram:
    if not data:
        data = str(uuid4())
    return Telegram(
        url=url,
        data=data,
        max_retries=3,
    )
