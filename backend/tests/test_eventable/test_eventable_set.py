from backend.shared.event_driven.eventable import Eventable, EventableSet, Property


class Foo(Eventable):
    value: int = 100
    inner_set: EventableSet[int] = Property(default_factory=EventableSet)


def test_foo():
    collection = EventableSet(key=lambda x: x.value, prevent_duplicates=True)

    foo1 = Foo()
    foo2 = Foo()
    foo3 = Foo()

    collection.add(foo1)
    collection.remove(foo1.value)
    assert len(collection.parse_events()) == 2

    collection.add(foo2)
    foo2.value = 500
    assert len(collection.parse_events()) == 2

    collection.add(foo3)
    foo3.value = 500
    foo3.value = 111
    collection.remove(foo3.value)
    assert len(collection.parse_events()) == 2


def test_bar():
    foo = Foo()
    foo.inner_set.add(5)

    events = foo.parse_events()
    assert len(events) == 1
