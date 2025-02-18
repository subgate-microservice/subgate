from typing import Callable

from backend.shared.event_driven.base_event import Event, FieldUpdated, ItemAdded, ItemUpdated, ItemRemoved
from backend.shared.utils import get_current_datetime
from backend.subscription.domain.discount import Discount
from backend.subscription.domain.events import (
    SubscriptionUpdated, SubscriptionUsageAdded, SubscriptionDiscountAdded,
    SubscriptionUsageUpdated, SubscriptionDiscountUpdated,
    SubscriptionUsageRemoved, SubscriptionDiscountRemoved,
    SubscriptionPaused, SubscriptionRenewed, SubscriptionResumed,
    SubscriptionExpired)
from backend.subscription.domain.subscription import Subscription, BillingInfo, PlanInfo, SubscriptionStatus
from backend.subscription.domain.usage import Usage


class SubscriptionEventParser:
    def __init__(self, subscription: Subscription):
        self.subscription = subscription
        self.updated_fields = set()
        self.result = []
        self.dt = get_current_datetime()

    def parse(self, events: list[Event]) -> list[Event]:
        for event in events:
            self._handle_event(event)

        if self.updated_fields:
            self.result.append(
                SubscriptionUpdated(
                    subscription_id=self.subscription.id,
                    changed_fields=tuple(self.updated_fields),
                    auth_id=self.subscription.auth_id,
                    occurred_at=self.dt
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
            Subscription: "{key}",
            Usage: "usages.{key}:updated",
            Discount: "discounts.{key}:updated",
            BillingInfo: "billing_info.{key}",
            PlanInfo: "plan_info.{key}"
        }

        key = event.field.lstrip("_")
        entity_type = type(event.entity)
        try:
            field_template = entity_field_map[entity_type]
            self.updated_fields.add(field_template.format(key=key))
        except KeyError:
            raise TypeError(entity_type)

    def _handle_item_added(self, event):
        if isinstance(event.item, Usage):
            self.updated_fields.add(f"usages.{event.item.code}:added")
            self.result.append(
                SubscriptionUsageAdded(
                    subscription_id=self.subscription.id, code=event.item.code, unit=event.item.unit,
                    available_units=event.item.available_units, auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )
        elif isinstance(event.item, Discount):
            self.updated_fields.add(f"discounts.{event.item.code}:added")
            self.result.append(
                SubscriptionDiscountAdded(
                    subscription_id=self.subscription.id, title=event.item.title, code=event.item.code,
                    size=event.item.size, valid_until=event.item.valid_until, description=event.item.description,
                    auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )

    def _handle_item_updated(self, event):
        if isinstance(event.new_item, Usage):
            self.updated_fields.add(f"usages.{event.new_item.code}:updated")
            self.result.append(
                SubscriptionUsageUpdated(
                    subscription_id=self.subscription.id, title=event.new_item.title, code=event.new_item.code,
                    unit=event.new_item.unit, available_units=event.new_item.available_units,
                    used_units=event.new_item.used_units,
                    delta=event.new_item.used_units - event.old_item.used_units,
                    auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )
        elif isinstance(event.new_item, Discount):
            self.updated_fields.add(f"discounts.{event.new_item.code}:updated")
            self.result.append(
                SubscriptionDiscountUpdated(
                    subscription_id=self.subscription.id, title=event.new_item.title, code=event.new_item.code,
                    size=event.new_item.size, valid_until=event.new_item.valid_until,
                    description=event.new_item.description, auth_id=self.subscription.auth_id, occurred_at=self.dt)
            )

    def _handle_item_removed(self, event):
        if isinstance(event.item, Usage):
            self.updated_fields.add(f"usages.{event.item.code}:removed")
            self.result.append(
                SubscriptionUsageRemoved(
                    subscription_id=self.subscription.id, code=event.item.code, auth_id=self.subscription.auth_id,
                    occurred_at=self.dt)
            )
        elif isinstance(event.item, Discount):
            self.updated_fields.add(f"discounts.{event.item.code}:removed")
            self.result.append(
                SubscriptionDiscountRemoved(
                    subscription_id=self.subscription.id, code=event.item.code, auth_id=self.subscription.auth_id,
                    occurred_at=self.dt)
            )


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
                    SubscriptionPaused(subscription_id=self.new_subscription.id, auth_id=self.new_subscription.auth_id,
                                       occurred_at=self.now, paused_from=self.new_subscription.paused_from)
                )
            elif self.new_subscription.status == SubscriptionStatus.Active:
                if self.old_subscription.status == SubscriptionStatus.Expired:
                    self.events.append(
                        SubscriptionRenewed(subscription_id=self.new_subscription.id,
                                            auth_id=self.new_subscription.auth_id, occurred_at=self.now,
                                            last_billing=self.new_subscription.billing_info.last_billing)
                    )
                elif self.old_subscription.status == SubscriptionStatus.Paused:
                    self.events.append(
                        SubscriptionResumed(subscription_id=self.new_subscription.id,
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
        changed_fields = []
        for field in ['plan_info.id', 'plan_info.title', 'plan_info.description', 'plan_info.level',
                      'plan_info.features', 'billing_info.price', 'billing_info.currency', 'billing_info.last_billing',
                      'billing_info.billing_cycle', 'status', 'paused_from', 'subscriber_id', 'autorenew', 'fields',
                      ]:
            old_value = eval(f'self.old_subscription.{field}')
            new_value = eval(f'self.new_subscription.{field}')
            if old_value != new_value:
                changed_fields.append(field)

        old_discounts = {d.code for d in self.old_subscription.discounts}
        new_discounts = {d.code for d in self.new_subscription.discounts}

        for code in new_discounts - old_discounts:
            changed_fields.append(f'discounts.{code}:added')
        for code in old_discounts - new_discounts:
            changed_fields.append(f'discounts.{code}:removed')
        for code in old_discounts.intersection(new_discounts):
            if self.old_subscription.discounts.get(code) != self.new_subscription.discounts.get(code):
                changed_fields.append(f'discounts.{code}:updated')

        old_usages = {u.code for u in self.old_subscription.usages}
        new_usages = {u.code for u in self.new_subscription.usages}

        for code in new_usages - old_usages:
            changed_fields.append(f'usages.{code}:added')
        for code in old_usages - new_usages:
            changed_fields.append(f'usages.{code}:removed')
        for code in old_usages.intersection(new_usages):
            if self.old_subscription.usages.get(code) != self.new_subscription.usages.get(code):
                changed_fields.append(f'usages.{code}:updated')

        if changed_fields:
            self.events.append(
                SubscriptionUpdated(subscription_id=self.new_subscription.id, changed_fields=tuple(changed_fields),
                                    auth_id=self.new_subscription.auth_id, occurred_at=self.now)
            )
