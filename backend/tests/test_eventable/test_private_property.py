import pytest

from backend.shared.event_driven.base_event import FieldUpdated
from backend.shared.event_driven.eventable import Eventable, PrivateProperty


class Foo(Eventable):
    _included: str = PrivateProperty(default="Hello", excluded=False)
    _excluded: str = PrivateProperty(default="World", excluded=True)


def test_access_to_included_private_property():
    foo = Foo()
    assert foo._included == "Hello"


def test_change_included_private_property():
    foo = Foo()
    foo._included = "Updated"
    assert foo._included == "Updated"

    events = foo.parse_events()
    assert len(events) == 1
    event = events.pop()
    assert isinstance(event, FieldUpdated)
    assert event.field == "_included"
    assert event.old_value == "Hello"
    assert event.new_value == "Updated"
    assert event.entity is foo


def test_access_to_excluded_private_property():
    foo = Foo()
    assert foo._excluded == "World"


def test_change_excluded_private_property():
    foo = Foo()
    foo._excluded = "Updated"
    assert foo._excluded == "Updated"

    events = foo.parse_events()
    assert len(events) == 1
    event = events.pop()
    assert isinstance(event, FieldUpdated)
    assert event.field == "_excluded"
    assert event.old_value == "World"
    assert event.new_value == "Updated"
    assert event.entity is foo


def test_included_property_with_constructor():
    foo = Foo(_included="BigBen")
    assert foo._included == "BigBen"


def test_excluded_property_with_constructor():
    with pytest.raises(AttributeError):
        _foo = Foo(_excluded="BigBen")
