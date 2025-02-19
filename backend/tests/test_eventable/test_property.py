from typing import Optional

import pytest

from backend.shared.event_driven.eventable import Eventable, Property


class Foo(Eventable):
    title: str
    frozen: str = Property(frozen=True)
    mapped: int = Property(mapper=lambda x: x ** 2, default=10)
    default_factory: str = Property(default_factory=lambda: "Hello World!")
    default: Optional[int] = Property(default=None)


def test_create_with_all_kwargs():
    foo = Foo(title="Foo", frozen="asd", mapped=4, default_factory="Argument", default=100)
    assert foo.title == "Foo"
    assert foo.frozen == "asd"
    assert foo.mapped == 16
    assert foo.default_factory == "Argument"
    assert foo.default == 100


def test_foo_without_title():
    with pytest.raises(AttributeError):
        _foo = Foo(frozen="asd", mapped=4, default_factory="Argument", default=100)


def test_create_with_defaults():
    foo = Foo(title="Foo", frozen=19)
    assert foo.frozen == 19
    assert foo.mapped == 100
    assert foo.default_factory == "Hello World!"
    assert foo.default is None


def test_change_frozen_attr_raises_error():
    foo = Foo(title="Foo", frozen=19)
    with pytest.raises(AttributeError):
        foo.frozen = 200


def test_miss_argument_on_property_without_default():
    with pytest.raises(AttributeError) as err:
        _foo = Foo(title="Foo")
    print(err.value)
