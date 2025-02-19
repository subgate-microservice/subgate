from backend.shared.event_driven.base_event import FieldUpdated
from backend.shared.event_driven.eventable import Eventable


class Bar(Eventable):
    value: int


class Foo(Eventable):
    title: str
    inner: Bar


def test_track_simple_value():
    bar = Bar(value=100)
    foo = Foo(title="Hello", inner=bar)

    foo.title = "Updated"
    events = foo.parse_events()
    assert len(events) == 1
    assert isinstance(events.pop(), FieldUpdated)


def test_track_inner_value():
    bar = Bar(value=100)
    foo = Foo(title="Hello", inner=bar)
    bar.value = 400

    events = foo.parse_events()
    assert len(events) == 1
    assert isinstance(events.pop(), FieldUpdated)


def test_replace_inner_value_into_other_trackable():
    bar1 = Bar(value=100)
    bar2 = Bar(value=200)
    foo = Foo(title="Hello", inner=bar1)

    bar1.value = 150  # Это изменение не имеет значения, потому что мы отвяжем bar1 от foo
    bar2.value = 250  # Это событие имеет значение, потому что мы присоединим bar2 к foo
    foo.inner = bar2

    # Должно быть два события
    # Первое - мы изменили Foo.inner_value
    # Второе - мы изменили само inner.value
    events = foo.parse_events()
    assert len(events) == 2
    for event in events:
        event: FieldUpdated
        if isinstance(event.entity, Foo):
            assert event.new_value is bar2
        if isinstance(event.entity, Bar):
            assert event.entity is bar2
            assert event.old_value == 200
            assert event.new_value == 250
