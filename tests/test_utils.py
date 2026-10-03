from datetime import date
from decimal import Decimal

import pytest

from app.utils import (
    email_is_valid,
    valid_date_range,
    valid_deposit_and_withdraw_amount,
    valid_dob,
    valid_num_shares,
    valid_password,
)


@pytest.mark.parametrize(
    "email, expected",
    [
        ("Student@Example.com", "student@example.com"),
        ("not-an-email", None),
        (None, False),
    ],
)
def test_email_validation(email, expected):
    assert email_is_valid(email) == expected


@pytest.mark.parametrize(
    "password, is_valid",
    [
        ("StudentPass1", True),
        ("short1A", False),
        ("alllowercase1", False),
        ("SymbolsAllowed!1", True),
        ("No Spaces Here1A", False),
    ],
)
def test_password_validation(password, is_valid):
    assert bool(valid_password(password)) is is_valid


def test_valid_dob_returns_date():
    assert valid_dob("2000-02-29") == date(2000, 2, 29)


@pytest.mark.parametrize("value", ["not-a-date", "2001-02-29", "", None])
def test_invalid_dob_is_rejected(value):
    assert valid_dob(value) is None


@pytest.mark.parametrize(
    "amount, expected",
    [
        ("10", Decimal("10.00")),
        ("1000000.00", Decimal("1000000.00")),
        ("9.99", None),
        ("10.001", None),
        ("not-a-number", None),
    ],
)
def test_cash_amount_validation(amount, expected):
    assert valid_deposit_and_withdraw_amount(amount) == expected


@pytest.mark.parametrize(
    "value, expected",
    [("1", 1), ("100000", 100000), ("0", None), ("100001", None), ("abc", None)],
)
def test_share_validation(value, expected):
    assert valid_num_shares(value) == expected


@pytest.mark.parametrize(
    "start_date, end_date, expected",
    [
        (None, None, True),
        ("2026-01-01", "2026-01-01", True),
        ("2026-01-01", "2026-01-31", True),
        ("2026-01-01", None, False),
        (None, "2026-01-31", False),
        ("invalid", "2026-01-31", False),
        ("2026-02-01", "2026-01-31", False),
    ],
)
def test_date_range_validation(start_date, end_date, expected):
    assert valid_date_range(start_date, end_date) is expected
