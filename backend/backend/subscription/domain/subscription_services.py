from typing import Callable, Optional

from backend.shared.event_driven.base_event import Event, FieldUpdated, ItemAdded, ItemUpdated, ItemRemoved
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.enums import SubscriptionStatus
from backend.subscription.domain.events import (
    SubscriptionUpdated, SubscriptionUsageAdded, SubscriptionDiscountAdded,
    SubscriptionUsageUpdated, SubscriptionDiscountUpdated,
    SubscriptionUsageRemoved, SubscriptionDiscountRemoved,
    SubscriptionPaused, SubscriptionRenewed, SubscriptionResumed,
    SubscriptionExpired)
from backend.subscription.domain.subscription import Subscription, BillingInfo, PlanInfo
from backend.subscription.domain.usage import Usage


class SubscriptionEventParser:
    def __init__(self, subscription: Subscription):
        self.subscription = subscription
        self.updated_fields = {}
        self.result = []
        self.dt = get_current_datetime()

    def parse(self, events: list[Event]) -> list[Event]:
        for event in events:
            self._handle_event(event)

        if self.updated_fields:
            self.result.append(
                SubscriptionUpdated(
                    id=self.subscription.id,
                    subscriber_id=self.subscription.subscriber_id,
                    changes=self.updated_fields,
                    auth_id=self.subscription.auth_id,
                    occurred_at=self.dt,
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

    def _handle_item_added(self, event):
        if isinstance(event.item, Usage):
            self.updated_fields[f"usages.{event.item.code}"] = "action:added"
            self.result.append(
                SubscriptionUsageAdded(
                    subscription_id=self.subscription.id, code=event.item.code, unit=event.item.unit,
                    available_units=event.item.available_units, auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )
        elif isinstance(event.item, Discount):
            self.updated_fields[f"discounts.{event.item.code}"] = "action:added"
            self.result.append(
                SubscriptionDiscountAdded(
                    subscription_id=self.subscription.id, title=event.item.title, code=event.item.code,
                    size=event.item.size, valid_until=event.item.valid_until, description=event.item.description,
                    auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )

    def _handle_item_updated(self, event):
        if isinstance(event.new_item, Usage):
            self.updated_fields[f"usages.{event.item.code}"] = "action:updated"
            self.result.append(
                SubscriptionUsageUpdated(
                    subscription_id=self.subscription.id, title=event.new_item.title, code=event.new_item.code,
                    unit=event.new_item.unit, available_units=event.new_item.available_units,
                    used_units=event.new_item.used_units,
                    delta=event.new_item.used_units - event.old_item.used_units,
                    auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )
        elif isinstance(event.new_item, Discount):
            self.updated_fields[f"discounts.{event.item.code}"] = "action:updated"
            self.result.append(
                SubscriptionDiscountUpdated(
                    subscription_id=self.subscription.id, title=event.new_item.title, code=event.new_item.code,
                    size=event.new_item.size, valid_until=event.new_item.valid_until,
                    description=event.new_item.description, auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )

    def _handle_item_removed(self, event):
        if isinstance(event.item, Usage):
            self.updated_fields[f"usages.{event.item.code}"] = "action:removed"
            self.result.append(
                SubscriptionUsageRemoved(
                    subscription_id=self.subscription.id, code=event.item.code, auth_id=self.subscription.auth_id,
                    occurred_at=self.dt)
            )
        elif isinstance(event.item, Discount):
            self.updated_fields[f"discounts.{event.item.code}"] = "action:removed"
            self.result.append(
                SubscriptionDiscountRemoved(
                    subscription_id=self.subscription.id, code=event.item.code, auth_id=self.subscription.auth_id,
                    occurred_at=self.dt)
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
            'subscriber_id',
            'autorenew',
            'fields',
        ]:
            old_value = eval(f'self.target.{field}')
            new_value = eval(f'self.new_data.{field}')
            if old_value != new_value:
                set_nested_attr(self.target, field, new_value)

    def _check_status_change(self):
        if self.target.status != self.new_data.status:
            if self.new_data.status == SubscriptionStatus.Paused:
                self.target.pause()
            elif self.new_data.status == SubscriptionStatus.Active:
                if self.target.status == SubscriptionStatus.Expired:
                    self.target.renew()
                elif self.target.status == SubscriptionStatus.Paused:
                    self.target.resume()
                else:
                    raise ValueError
            elif self.new_data.status == SubscriptionStatus.Expired:
                self.target.expire()

    def update(self, new_data: Subscription):
        self.new_data = new_data
        self._check_usages()
        self._check_discounts()
        self._check_status_change()
        self._check_field_updates()


class SubscriptionUpdatesEventGenerator:
    def __init__(self, old_subscription: Subscription, new_subscription: Subscription):
        self.old_subscription = old_subscription
        self.new_subscription = new_subscription
        self.events = []
        self.now = get_current_datetime()

    def generate_events(self) -> list[Event]:
        self.now = get_current_datetime()
        self._check_status_change()
        self._check_discounts()
        self._check_usages()
        self._check_general_updates()
        events = self.events
        self.events = []
        return events

    def _check_status_change(self):
        if self.old_subscription.status != self.new_subscription.status:
            if self.new_subscription.status == SubscriptionStatus.Paused:
                self.events.append(
                    SubscriptionPaused(
                        id=self.new_subscription.id,
                        subscriber_id=self.new_subscription.subscriber_id,
                        auth_id=self.new_subscription.auth_id,
                        occurred_at=self.now,
                    )
                )
            elif self.new_subscription.status == SubscriptionStatus.Active:
                if self.old_subscription.status == SubscriptionStatus.Expired:
                    self.events.append(
                        SubscriptionRenewed(
                            id=self.new_subscription.id,
                            subscriber_id=self.new_subscription.subscriber_id,
                            auth_id=self.new_subscription.auth_id,
                            occurred_at=self.now,
                            last_billing=self.new_subscription.billing_info.last_billing,
                        )
                    )
                elif self.old_subscription.status == SubscriptionStatus.Paused:
                    self.events.append(
                        SubscriptionResumed(id=self.new_subscription.id,
                                            subscriber_id=self.new_subscription.subscriber_id,
                                            auth_id=self.new_subscription.auth_id, occurred_at=self.now)
                    )
                else:
                    raise ValueError
            elif self.new_subscription.status == SubscriptionStatus.Expired:
                self.events.append(
                    SubscriptionExpired(subscription_id=self.new_subscription.id, auth_id=self.new_subscription.auth_id,
                                        occurred_at=self.now))

    def _check_discounts(self):
        old_discounts = {d.code: d for d in self.old_subscription.discounts}
        new_discounts = {d.code: d for d in self.new_subscription.discounts}

        for code, new_discount in new_discounts.items():
            if code not in old_discounts:
                self.events.append(
                    SubscriptionDiscountAdded(subscription_id=self.new_subscription.id, title=new_discount.title,
                                              code=new_discount.code, size=new_discount.size,
                                              valid_until=new_discount.valid_until,
                                              description=new_discount.description,
                                              auth_id=self.new_subscription.auth_id, occurred_at=self.now))
            elif old_discounts[code] != new_discount:
                self.events.append(
                    SubscriptionDiscountUpdated(subscription_id=self.new_subscription.id, title=new_discount.title,
                                                code=new_discount.code, size=new_discount.size,
                                                valid_until=new_discount.valid_until,
                                                description=new_discount.description,
                                                auth_id=self.new_subscription.auth_id, occurred_at=self.now))

        for code in old_discounts:
            if code not in new_discounts:
                self.events.append(SubscriptionDiscountRemoved(subscription_id=self.new_subscription.id, code=code,
                                                               auth_id=self.new_subscription.auth_id,
                                                               occurred_at=self.now))

    def _check_usages(self):
        old_usages = {u.code: u for u in self.old_subscription.usages}
        new_usages = {u.code: u for u in self.new_subscription.usages}

        for code, new_usage in new_usages.items():
            if code not in old_usages:
                self.events.append(SubscriptionUsageAdded(subscription_id=self.new_subscription.id, code=new_usage.code,
                                                          unit=new_usage.unit,
                                                          available_units=new_usage.available_units,
                                                          auth_id=self.new_subscription.auth_id, occurred_at=self.now))
            else:
                old_usage = old_usages[code]
                if old_usage.available_units != new_usage.available_units or old_usage.used_units != new_usage.used_units:
                    delta = new_usage.used_units - old_usage.used_units
                    self.events.append(
                        SubscriptionUsageUpdated(subscription_id=self.new_subscription.id, title=new_usage.title,
                                                 code=new_usage.code, unit=new_usage.unit,
                                                 available_units=new_usage.available_units,
                                                 used_units=new_usage.used_units, delta=delta,
                                                 auth_id=self.new_subscription.auth_id, occurred_at=self.now))

        for code in old_usages:
            if code not in new_usages:
                self.events.append(SubscriptionUsageRemoved(subscription_id=self.new_subscription.id, code=code,
                                                            auth_id=self.new_subscription.auth_id,
                                                            occurred_at=self.now))

    def _check_general_updates(self):
        changed_fields = {}
        for field in ['plan_info.id', 'plan_info.title', 'plan_info.description', 'plan_info.level',
                      'plan_info.features', 'billing_info.price', 'billing_info.currency', 'billing_info.last_billing',
                      'billing_info.billing_cycle', 'status', 'paused_from', 'subscriber_id', 'autorenew', 'fields',
                      ]:
            old_value = eval(f'self.old_subscription.{field}')
            new_value = eval(f'self.new_subscription.{field}')
            if old_value != new_value:
                changed_fields[field] = new_value

        old_discounts = {d.code for d in self.old_subscription.discounts}
        new_discounts = {d.code for d in self.new_subscription.discounts}

        for code in new_discounts - old_discounts:
            changed_fields[f'discounts.{code}'] = 'action:added'
        for code in old_discounts - new_discounts:
            changed_fields[f'discounts.{code}'] = 'action:removed'
        for code in old_discounts.intersection(new_discounts):
            if self.old_subscription.discounts.get(code) != self.new_subscription.discounts.get(code):
                changed_fields[f'discounts.{code}'] = 'action:updated'

        old_usages = {u.code for u in self.old_subscription.usages}
        new_usages = {u.code for u in self.new_subscription.usages}

        for code in new_usages - old_usages:
            changed_fields[f'usages.{code}'] = 'action:added'
        for code in old_usages - new_usages:
            changed_fields[f'usages.{code}'] = 'action:removed'
        for code in old_usages.intersection(new_usages):
            if self.old_subscription.usages.get(code) != self.new_subscription.usages.get(code):
                changed_fields[f'usages.{code}'] = 'action:updated'

        if changed_fields:
            self.events.append(
                SubscriptionUpdated(id=self.new_subscription.id, subscriber_id=self.new_subscription.subscriber_id,
                                    changes=changed_fields, auth_id=self.new_subscription.auth_id, occurred_at=self.now)
            )
