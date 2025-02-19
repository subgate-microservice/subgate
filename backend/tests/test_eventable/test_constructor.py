import pytest

from backend.shared.event_driven.eventable import Eventable


class Foo(Eventable):
    title: str
    value: int


def test_not_events_in_initialisation():
    foo = Foo(title="Hello", value=400)
    events = foo.parse_events()
    assert len(events) == 0


def test_extra_kwargs_in_initialization():
    with pytest.raises(AttributeError):
        foo = Foo(title="Hello", value=500, extra=100)


def test_lack_kwargs_in_initialization():
    with pytest.raises(AttributeError):
        _foo = Foo(title="Hello")
