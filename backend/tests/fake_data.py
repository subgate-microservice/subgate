from uuid import uuid4

from pydantic import AwareDatetime

from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthUser
from backend.subscription.domain.plan import Plan, UsageOld, UsageRateOld
from backend.webhook.domain.telegram import Telegram


def create_plan(auth_user: AuthUser = None, title="Business", level=10, usage_rates: list[UsageRateOld] = None):
    raise NotImplemented


def create_subscription(
        plan: Plan = None,
        subscriber_id: str = None,
        usages: list[UsageOld] = None,
        auth_user: AuthUser = None,
        last_billing: AwareDatetime = None,
):
    raise NotImplemented


def create_webhook():
    raise NotImplemented


def create_apikey(auth_user: AuthUser = None):
    if auth_user is None:
        auth_user = AuthUser(id=uuid4())
    return Apikey(
        title=f"Title_{uuid4()}",
        auth_user=auth_user,
    )


def create_telegraph_message(url: str, data: str = None) -> Telegram:
    raise NotImplemented
