"""Boundary-focused suite written to catch off-by-one and operator bugs."""
import pytest
from pricing import apply_discount, clamp, is_leap_year


@pytest.mark.parametrize("x,expected", [(-1, 0), (0, 0), (5, 5), (10, 10), (11, 10)])
def test_clamp(x, expected):
    assert clamp(x, 0, 10) == expected


def test_clamp_returns_bounds_not_input():
    assert clamp(-5, 2, 8) == 2
    assert clamp(50, 2, 8) == 8


@pytest.mark.parametrize("year,expected", [
    (2024, True), (2023, False), (1900, False), (2000, True), (2100, False), (1, False), (4, True),
])
def test_leap_year(year, expected):
    assert is_leap_year(year) is expected


def test_discount_values():
    assert apply_discount(100, 10) == 90
    assert apply_discount(19.99, 15) == 16.99
    assert apply_discount(50, 0) == 50
    assert apply_discount(50, 100) == 0
    assert apply_discount(80, 25) == 60


@pytest.mark.parametrize("bad", [-1, 101])
def test_discount_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        apply_discount(10, bad)
