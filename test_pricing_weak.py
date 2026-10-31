"""A typical 'happy path only' suite: all green, but it barely checks anything."""
from pricing import apply_discount, clamp, is_leap_year


def test_clamp_runs():
    assert clamp(5, 0, 10) == 5


def test_leap_year():
    assert is_leap_year(2024)


def test_discount():
    assert apply_discount(100, 10) == 90
