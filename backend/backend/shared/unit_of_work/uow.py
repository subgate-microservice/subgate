from abc import ABC, abstractmethod
from typing import Self

from backend.auth.domain.apikey_repo import ApikeyRepo
from backend.shared.event_driven.base_event import Event
from backend.subscription.domain.plan_repo import PlanRepo
from backend.subscription.domain.subscription_repo import SubscriptionRepo
from backend.webhook.domain.telegram import TelegramRepo
from backend.webhook.domain.webhook_repo import WebhookRepo


class UnitOfWork(ABC):
    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass

    @abstractmethod
    def push_event(self, event: Event) -> None:
        pass

    @abstractmethod
    def parse_events(self) -> list[Event]:
        pass

    @abstractmethod
    def subscription_repo(self) -> SubscriptionRepo:
        pass

    @abstractmethod
    def plan_repo(self) -> PlanRepo:
        pass

    @abstractmethod
    def webhook_repo(self) -> WebhookRepo:
        pass

    @abstractmethod
    def apikey_repo(self) -> ApikeyRepo:
        pass

    @abstractmethod
    def telegram_repo(self) -> TelegramRepo:
        pass

    @abstractmethod
    async def __aenter__(self) -> Self:
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        pass


class UnitOfWorkFactory(ABC):
    @abstractmethod
    def create_uow(self, *args, **kwargs) -> UnitOfWork:
        pass
