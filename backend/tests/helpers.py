from datetime import datetime, timedelta


def is_close_datetime(dt1: datetime, dt2: datetime, abs_tol: timedelta = timedelta(seconds=1)) -> bool:
    return abs((dt1 - dt2).total_seconds()) <= abs_tol.total_seconds()


def is_equal(value1, value2):
    if isinstance(value1, datetime) and isinstance(value2, datetime):
        return is_close_datetime(value1, value2)

    return value1 == value2


def check_changes(real: dict, expected: dict):
    real_keys = set(real.keys())
    expected_keys = set(expected.keys())

    assert real_keys == expected_keys

    for key in real_keys:
        real_value = real.get(key)
        expected_value = expected.get(key)
        assert is_equal(real_value, expected_value)
