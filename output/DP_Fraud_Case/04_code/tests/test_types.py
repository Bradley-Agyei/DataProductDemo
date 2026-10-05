from datetime import date, datetime
from decimal import Decimal

import pytest

from src.dp_framework.contract import Column
from src.dp_framework.types import ParseError, parse_decimal, parse_value


@pytest.mark.parametrize("raw, expected", [
    ("$500.00 ", Decimal("500.00")),
    ("$1,225.35 ", Decimal("1225.35")),
    ("($199.78)", Decimal("-199.78")),
    ("-12.5", Decimal("-12.50")),
    ("0", Decimal("0.00")),
])
def test_currency_text_becomes_decimal(raw, expected):
    assert parse_decimal(raw, scale=2) == expected


def test_non_numeric_currency_is_rejected():
    with pytest.raises(ParseError):
        parse_decimal("abc", scale=2)


def test_decimal_precision_is_enforced():
    with pytest.raises(ParseError):
        parse_value("12345.00", Column("x", "DECIMAL(5,2)"))


@pytest.mark.parametrize("physical, raw, expected", [
    ("DATE", "1/8/2019", date(2019, 1, 8)),
    ("DATE", "2019-01-08", date(2019, 1, 8)),
    ("TIMESTAMP", "9/2/2026 9:01", datetime(2026, 9, 2, 9, 1)),
    ("BOOLEAN", "TRUE", True),
    ("BOOLEAN", "false", False),
    ("INT", "20260921", 20260921),
    ("SMALLINT", "2026", 2026),
    ("CHAR(5)", "12345", "12345"),
    ("VARCHAR(10)", " A00001 ", "A00001"),
])
def test_parse_value_by_type(physical, raw, expected):
    assert parse_value(raw, Column("x", physical)) == expected


@pytest.mark.parametrize("physical, raw", [
    ("BOOLEAN", "maybe"),
    ("DATE", "31/31/2020"),
    ("INT", "12.5"),
    ("SMALLINT", "70000"),
    ("CHAR(2)", "NCX"),
    ("VARCHAR(3)", "ABCD"),
])
def test_invalid_values_raise(physical, raw):
    with pytest.raises(ParseError):
        parse_value(raw, Column("x", physical))


def test_blank_is_null():
    assert parse_value("  ", Column("x", "DECIMAL(15,2)", nullable=True)) is None


def test_postal_code_keeps_leading_zero():
    assert parse_value("02101", Column("x", "CHAR(5)")) == "02101"
