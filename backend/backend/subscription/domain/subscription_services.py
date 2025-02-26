from typing import Callable, Optional, Union

from loguru import logger

from backend.shared.event_driven.base_event import Event, FieldUpdated, ItemAdded, ItemUpdated, ItemRemoved
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.enums import SubscriptionStatus
from backend.subscription.domain.events import (
    SubUpdated, SubUsageAdded, SubDiscountAdded,
    SubUsageUpdated, SubDiscountUpdated,
    SubUsageRemoved, SubDiscountRemoved)
from backend.subscription.domain.subscription import Subscription, BillingInfo, PlanInfo
from backend.subscription.domain.usage import Usage


def find_changes(old_version: Union[Usage, Discount], new_version: Union[Usage, Discount]):
    result = {}
    for key in old_version.__class__.__annotations__:
        old_value, new_value = getattr(old_version, key), getattr(new_version, key)
        if old_value != new_value:
            result[key] = new_value
    return result


class SubscriptionEventParser:
    def __init__(self, subscription: Subscription):
        self.subscription = subscription
        self.updated_fields = {}
        self.result = []

    def parse(self, events: list[Event]) -> list[Event]:
        for event in events:
            self._handle_event(event)

        if self.updated_fields:
            self.result.append(
                SubUpdated(
                    id=self.subscription.id,
                    subscriber_id=self.subscription.subscriber_id,
                    changes=self.updated_fields,
                    auth_id=self.subscription.auth_id,
                    occurred_at=get_current_datetime(),
                )
            )
        return self.result

    def _handle_event(self, event):
        event_handlers = {
            FieldUpdated: self._handle_field_updated,
            ItemAdded: self._handle_item_added,
            ItemUpdated: self._handle_item_updated,
            ItemRemoved: self._handle_item_removed
        }

        handler: Callable = event_handlers.get(type(event))
        if handler:
            handler(event)
        else:
            self.result.append(event)

    def _handle_field_updated(self, event: FieldUpdated):
        entity_field_map = {
            Subscription: ("{key}", event.new_value),
            Usage: ("usages.{key}", "action:updated"),
            Discount: ("discounts.{key}", "action:updated"),
            BillingInfo: ("billing_info.{key}", event.new_value),
            PlanInfo: ("plan_info.{key}", event.new_value),
        }

        key = event.field.lstrip("_")
        entity_type = type(event.entity)
        try:
            field_template, value = entity_field_map[entity_type]
            key = field_template.format(key=key)
            self.updated_fields[key] = value
        except KeyError:
            raise TypeError(entity_type)

    def _handle_item_added(self, event: ItemAdded):
        if isinstance(event.item, Usage):
            self.updated_fields[f"usages.{event.item.code}"] = "action:added"
            self.result.append(
                SubUsageAdded(
                    subscription_id=self.subscription.id,
                    title=event.item.title,
                    code=event.item.code,
                    unit=event.item.unit,
                    available_units=event.item.available_units,
                    renew_cycle=event.item.renew_cycle,
                    used_units=event.item.used_units,
                    last_renew=event.item.last_renew,
                    auth_id=self.subscription.auth_id,
                    occurred_at=event.occurred_at,
                )
            )
        elif isinstance(event.item, Discount):
            self.updated_fields[f"discounts.{event.item.code}"] = "action:added"
            self.result.append(
                SubDiscountAdded(
                    subscription_id=self.subscription.id,
                    title=event.item.title,
                    code=event.item.code,
                    description=event.item.description,
                    size=event.item.size,
                    valid_until=event.item.valid_until,
                    auth_id=self.subscription.auth_id,
                    occurred_at=event.occurred_at,
                )
            )

    def _handle_item_updated(self, event: ItemUpdated):
        if isinstance(event.new_item, Usage):
            self.updated_fields[f"usages.{event.new_item.code}"] = "action:updated"
            self.result.append(
                SubUsageUpdated(
                    subscription_id=self.subscription.id,
                    code=event.new_item.code,
                    changes=find_changes(event.old_item, event.new_item),
                    delta=event.new_item.used_units - event.old_item.used_units,
                    occurred_at=event.occurred_at,
                    auth_id=self.subscription.auth_id,
            )
            )
        elif isinstance(event.new_item, Discount):
            self.updated_fields[f"discounts.{event.new_item.code}"] = "action:updated"
            self.result.append(
                SubDiscountUpdated(
                    subscription_id=self.subscription.id,
                    code=event.new_item.code,
                    changes=find_changes(event.old_item, event.new_item),
                    occurred_at=event.occurred_at,
                    auth_id=self.subscription.auth_id,
                )
            )

    def _handle_item_removed(self, event: ItemRemoved):
        if isinstance(event.item, Usage):
            self.updated_fields[f"usages.{event.item.code}"] = "action:removed"
            self.result.append(
                SubUsageRemoved(
                    subscription_id=self.subscription.id,
                    title=event.item.title,
                    code=event.item.code,
                    unit=event.item.unit,
                    available_units=event.item.available_units,
                    renew_cycle=event.item.renew_cycle,
                    used_units=event.item.used_units,
                    last_renew=event.item.last_renew,
                    auth_id=self.subscription.auth_id,
                    occurred_at=event.occurred_at,
                )
            )
        elif isinstance(event.item, Discount):
            self.updated_fields[f"discounts.{event.item.code}"] = "action:removed"
            self.result.append(
                SubDiscountRemoved(
                    subscription_id=self.subscription.id,
                    title=event.item.title,
                    code=event.item.code,
                    description=event.item.description,
                    size=event.item.size,
                    valid_until=event.item.valid_until,
                    auth_id=self.subscription.auth_id,
                    occurred_at=event.occurred_at,
                )
            )


def set_nested_attr(obj, attr_path, value):
    attrs = attr_path.split(".")
    for attr in attrs[:-1]:  # Проходим по всем, кроме последнего
        obj = getattr(obj, attr)  # Переходим внутрь объекта
    setattr(obj, attrs[-1], value)


class SubscriptionUpdater:
    def __init__(self, target_subscription: Subscription):
        self.target = target_subscription
        self.new_data: Optional[Subscription] = None

    def _check_discounts(self):
        old_discounts = {d.code: d for d in self.target.discounts}
        new_discounts = {d.code: d for d in self.new_data.discounts}

        for code, new_discount in new_discounts.items():
            if code not in old_discounts:
                self.target.discounts.add(new_discount)

        for code in old_discounts:
            if code not in new_discounts:
                self.target.discounts.remove(code)

        exist_discount_codes = set(old_discounts.keys()).intersection(new_discounts.keys())
        for code in exist_discount_codes:
            if old_discounts[code] != new_discounts[code]:
                self.target.discounts.update(new_discounts[code])

    def _check_usages(self):
        old_usages = {d.code: d for d in self.target.usages}
        new_usages = {d.code: d for d in self.new_data.usages}

        for code, new_usage in new_usages.items():
            if code not in old_usages:
                self.target.usages.add(new_usage)

        for code in old_usages:
            if code not in new_usages:
                self.target.usages.remove(code)

        exist_usage_codes = set(old_usages.keys()).intersection(new_usages.keys())
        for code in exist_usage_codes:
            if old_usages[code] != new_usages[code]:
                self.target.usages.update(new_usages[code])

    def _check_field_updates(self):
        for field in [
            'plan_info.id',
            'plan_info.title',
            'plan_info.description',
            'plan_info.level',
            'plan_info.features',

            'billing_info.price',
            'billing_info.currency',
            'billing_info.last_billing',
            'billing_info.billing_cycle',
            'billing_info.saved_days',

            '_status',
            '_paused_from',
            'updated_at',
            'subscriber_id',
            'autorenew',
            'fields',
        ]:
            old_value = eval(f'self.target.{field}')
            new_value = eval(f'self.new_data.{field}')
            if old_value != new_value:
                set_nested_attr(self.target, field, new_value)

    def _check_status_change(self):
        old_status, new_status = self.target.status, self.new_data.status
        last_billing_changed = self.target.billing_info.last_billing != self.new_data.billing_info.last_billing

        if last_billing_changed:
            if new_status != SubscriptionStatus.Active:
                raise Exception(f"Status must be 'Active' when you renewing the subscription")
            self.target.renew(self.new_data.billing_info.last_billing)
            return

        if old_status == new_status:
            return

        match (old_status, new_status):

            case (SubscriptionStatus.Paused, SubscriptionStatus.Active):
                self.target.resume()

            case (SubscriptionStatus.Active, SubscriptionStatus.Paused):
                self.target.pause()

            case (SubscriptionStatus.Active, SubscriptionStatus.Expired):
                self.target.expire()

            case (SubscriptionStatus.Expired, SubscriptionStatus.Active):
                self.target.renew(self.new_data.billing_info.last_billing)

            case (SubscriptionStatus.Paused, SubscriptionStatus.Expired):
                self.target.expire()

            case _:
                raise Exception(f"Invalid state transaction: {old_status} => {new_status}")

    def update(self, new_data: Subscription):
        self.new_data = new_data
        self._check_usages()
        self._check_discounts()
        self._check_status_change()
        self._check_field_updates()
