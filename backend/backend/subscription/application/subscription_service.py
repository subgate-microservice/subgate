from backend.shared.context import Context
from backend.shared.eventbus import Eventbus, Event
from backend.shared.events import EventCode
from backend.shared.unit_of_work.uow import UnitOfWork
from backend.subscription.domain.subscription import Subscription, SubscriptionUpdatesEventGenerator


class BaseService:
    def __init__(
            self,
            bus: Eventbus,
            uow: UnitOfWork,
    ):
        self._bus = bus
        self._uow = uow
        self._events: list[Event] = []

    def _add_event(self, code: EventCode, payload: Subscription):
        self._events.append(Event(code=code, payload=payload, context=Context(uow=self._uow)))

    async def send_events(self):
        for event in self._events:
            await self._bus.publish(event)
        self._events = []


class SubscriptionPartialUpdateService(BaseService):
    pass


class SubscriptionService(BaseService):
    pass


async def create_subscription(item: Subscription, uow: UnitOfWork) -> None:
    current_sub = await uow.subscription_repo().get_subscriber_active_one(
        subscriber_id=item.subscriber_id, auth_id=item.auth_id,
    )

    if current_sub:
        # Если создаваемая подписка старше текущей, то ставим на паузу текущую подписку
        if item.plan_info.level > current_sub.plan_info.level:
            new_version = current_sub.copy()
            new_version.pause()
            await update_subscription(current_sub, new_version, uow)
        # Если создаваемая подписка идентична или младше текущей, то ставим создаваемую подписку на паузу
        else:
            item.pause()

    await uow.subscription_repo().add_one(item)


async def update_subscription(old_sub: Subscription, new_sub: Subscription, uow: UnitOfWork) -> None:
    await uow.subscription_repo().update_one(new_sub)
    events = SubscriptionUpdatesEventGenerator(old_sub, new_sub).generate_events()
    for ev in events:
        uow.push_event(ev)
