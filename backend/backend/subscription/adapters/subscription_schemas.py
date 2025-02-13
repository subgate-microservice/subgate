from typing import Optional
from uuid import uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.subscription.domain.plan import UsageOld, Discount
from backend.subscription.domain.subscription import SubId, Subscription, SubscriptionStatus, BillingInfo, PlanInfo


class SubscriptionCreate(MyBase):
    id: SubId = Field(default_factory=uuid4)
    subscriber_id: str
    plan_info: PlanInfo
    billing_info: BillingInfo
    status: SubscriptionStatus = SubscriptionStatus.Active
    paused_from: Optional[AwareDatetime] = None
    autorenew: bool = False
    usages: list[UsageOld] = Field(default_factory=list)
    discounts: list[Discount] = Field(default_factory=list)
    fields: dict = Field(default_factory=dict)

    def to_subscription(self, auth_id: AuthId) -> Subscription:
        return Subscription(
            id=self.id,
            subscriber_id=self.subscriber_id,
            plan_info=self.plan_info,
            billing_info=self.billing_info,
            status=self.status,
            paused_from=self.paused_from,
            autorenew=self.autorenew,
            usages=self.usages,
            discounts=self.discounts,
            fields=self.fields,
            auth_id=auth_id,
        )


class SubscriptionUpdate(MyBase):
    id: SubId
    subscriber_id: str
    plan_info: PlanInfo
    billing_info: BillingInfo
    status: SubscriptionStatus
    paused_from: Optional[AwareDatetime]
    autorenew: bool
    usages: list[UsageOld]
    discounts: list[Discount]
    fields: dict

    def to_subscription(self, auth_id: AuthId, created_at: AwareDatetime) -> Subscription:
        return Subscription(
            id=self.id,
            subscriber_id=self.subscriber_id,
            plan_info=self.plan_info,
            billing_info=self.billing_info,
            status=self.status,
            paused_from=self.paused_from,
            autorenew=self.autorenew,
            usages=self.usages,
            discounts=self.discounts,
            fields=self.fields,
            auth_id=auth_id,
            created_at=created_at,
        )
