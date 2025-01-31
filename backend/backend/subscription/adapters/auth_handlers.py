from backend.auth.domain.auth_user import AuthUser
from backend.shared.context import Context
from backend.shared.eventbus import Event
from backend.subscription.application.plan_service import PlanService
from backend.subscription.application.subscription_service import SubscriptionService
from backend.subscription.domain.plan_repo import PlanSby
from backend.subscription.domain.subscription_repo import SubscriptionSby


async def handle_auth_user_deleted(event: Event[AuthUser, Context]) -> None:
    sby = SubscriptionSby(auth_ids={event.payload.id})
    await SubscriptionService(event.context.eventbus, event.context.uow).delete_selected(sby)

    sby = PlanSby(auth_ids={event.payload.id})
    await PlanService(event.context.eventbus, event.context.uow).delete_selected(sby)
