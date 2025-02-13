import dataclasses
from datetime import timedelta
from typing import Any, Optional, Self
from uuid import UUID, uuid4

from pydantic import Field, AwareDatetime

from backend.auth.domain.auth_user import AuthId
from backend.shared.base_models import MyBase
from backend.shared.event_driven.base_event import Event
from backend.shared.item_maanger import ItemManager
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.cycle import Period
from backend.subscription.domain.usage import UsageRate

PlanId = UUID


class UsageOld(MyBase):
    title: str
    code: str
    unit: str
    available_units: float
    renew_cycle: Period
    last_renew: AwareDatetime = Field(default_factory=get_current_datetime)
    used_units: float

    def renew(self) -> Self:
        return self.model_copy(update={
            "used_units": 0,
            "last_renew": get_current_datetime(),
        })

    @property
    def need_to_renew(self) -> bool:
        return get_current_datetime() > self.renew_cycle.get_next_billing_date(self.last_renew)

    @property
    def next_renew(self) -> AwareDatetime:
        return self.last_renew + timedelta(self.renew_cycle.get_cycle_in_days())


class UsageRateOld(MyBase):
    code: str
    title: str
    unit: str
    available_units: float
    renew_cycle: Period

    @classmethod
    def from_usage(cls, usage: UsageOld):
        return cls(code=usage.code, title=usage.title, unit=usage.unit, available_units=usage.available_units,
                   renew_cycle=usage.renew_cycle)


class Discount(MyBase):
    title: str
    code: str
    description: Optional[str] = None
    size: float = Field(ge=0, le=1)
    valid_until: Optional[AwareDatetime]


class PlanOld:
    id: PlanId = Field(default_factory=uuid4)
    title: str
    price: float
    currency: str
    billing_cycle: Period
    description: Optional[str] = None
    level: int = 1
    features: Optional[str] = None
    usage_rates: list[UsageRateOld] = Field(default_factory=list, )
    fields: dict[str, Any] = Field(default_factory=dict)
    auth_id: AuthId = Field(exclude=True)
    discounts: list[Discount] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=get_current_datetime)
    updated_at: AwareDatetime = Field(default_factory=get_current_datetime)


@dataclasses.dataclass(frozen=True)
class PlanCreated(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId
    created_at: AwareDatetime


@dataclasses.dataclass(frozen=True)
class PlanDeleted(Event):
    id: PlanId
    title: str
    price: float
    currency: str
    billing_cycle: Period
    auth_id: AuthId
    created_at: AwareDatetime


class Plan:
    def __init__(
            self,
            id: PlanId,
            title: str,
            price: float,
            currency: str,
            billing_cycle: Period,
            description: Optional[str],
            level: int,
            features: Optional[str],
            usage_rates: list[UsageRate],
            discounts: list[Discount],
            fields: dict[str, Any],
            auth_id: AuthId,
            created_at: AwareDatetime,
            updated_at: AwareDatetime,
    ):
        self._id = id
        self._title = title
        self._price = price
        self._currency = currency
        self._billing_cycle = billing_cycle
        self._description = description
        self._level = level
        self._features = features
        self._usage_rates = ItemManager(usage_rates, "code")
        self._discounts = ItemManager(discounts, "code")
        self._fields = fields
        self._auth_id = auth_id
        self._created_at = created_at
        self._updated_at = updated_at

        self._events: set[Event] = set()

    @property
    def title(self):
        return self._title

    @property
    def price(self):
        return self._price

    @property
    def currency(self):
        return self._currency

    @property
    def billing_cycle(self):
        return self._billing_cycle

    @property
    def description(self):
        return self._description

    @property
    def level(self):
        return self._level

    @property
    def fields(self):
        return self._fields

    @property
    def auth_id(self):
        return self._auth_id

    @property
    def created_at(self):
        return self._created_at

    @property
    def updated_at(self):
        return self._updated_at

    @property
    def features(self):
        return self._features

    @classmethod
    def create(
            cls,
            title: str,
            price: float,
            currency: str,
            auth_id: AuthId,
            billing_cycle: Period = Period.Monthly,
            description: str = None,
            level: int = 10,
            features: str = None,
            usage_rates: list[UsageRate] = None,
            discounts: list[Discount] = None,
            fields: dict = None,
            id: PlanId = None,
    ) -> Self:
        dt = get_current_datetime()
        id = id if id else uuid4()
        fields = fields if fields is not None else {}
        usage_rates = usage_rates if usage_rates is not None else []
        discounts = discounts if discounts is not None else []
        instance = cls(id, title, price, currency, billing_cycle, description, level, features, usage_rates, discounts,
                       fields, auth_id, dt, dt)
        event = PlanCreated(id, title, price, currency, billing_cycle, auth_id, dt)
        instance.push_event(event)
        return instance

    def delete(self):
        self._updated_at = get_current_datetime()
        self._events.add(
            PlanDeleted(self._id, self._title, self._price, self._currency, self._billing_cycle, self._auth_id,
                        self._updated_at)
        )

    def get_all_usage_rates(self) -> list[UsageRate]:
        return self._usage_rates.get_all()

    def get_usage_rate(self, code: str) -> UsageRate:
        return self._usage_rates.get(code)

    def add_usage_rate(self, usage_rate: UsageRate) -> None:
        self._usage_rates.add(usage_rate)
        self._updated_at = get_current_datetime()

    def update_usage_rate(self, usage_rate: UsageRate) -> None:
        self._usage_rates.update(usage_rate)
        self._updated_at = get_current_datetime()

    def remove_usage_rate(self, code: str) -> None:
        self._usage_rates.remove(code)
        self._updated_at = get_current_datetime()

    def get_discount(self, code: str) -> Discount:
        return self._discounts.get(code)

    def get_all_discounts(self) -> list[Discount]:
        return self._discounts.get_all()

    def add_discount(self, discount: Discount) -> None:
        self._discounts.add(discount)
        self._updated_at = get_current_datetime()

    def update_discount(self, discount: Discount) -> None:
        self._discounts.update(discount)
        self._updated_at = get_current_datetime()

    def remove_discount(self, code: str) -> None:
        self._discounts.remove(code)
        self._updated_at = get_current_datetime()

    def parse_events(self) -> set[Event]:
        events = self._events
        self._events = set()
        return events

    def push_event(self, event: Event) -> None:
        self._events.add(event)
