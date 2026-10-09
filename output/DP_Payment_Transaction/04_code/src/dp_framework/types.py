"""Parse raw source text into typed Python values, driven by a contract column's physical type."""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .contract import Column

DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d")
TIMESTAMP_FORMATS = ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")
TRUE_VALUES = {"TRUE", "T", "Y", "YES", "1"}
FALSE_VALUES = {"FALSE", "F", "N", "NO", "0"}
INT_RANGES = {"SMALLINT": (-32_768, 32_767), "INT": (-2_147_483_648, 2_147_483_647)}
_INT_RE = re.compile(r"[+-]?\d+")


class ParseError(ValueError):
    """A raw value cannot be converted to its contract type."""


def parse_decimal(raw: str, scale: int, precision: int = 38) -> Decimal:
    """Accepts accounting text: '$1,225.35 ' -> 1225.35 and '($199.78)' -> -199.78."""
    text = raw.strip().replace("$", "").replace(",", "").replace(" ", "")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ParseError(f"not a number: {raw!r}") from None
    if not value.is_finite():
        raise ParseError(f"not a finite number: {raw!r}")
    value = value.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)
    if value != 0 and value.adjusted() >= precision - scale:
        raise ParseError(f"{raw!r} exceeds DECIMAL({precision},{scale})")
    return -value if negative else value


def _parse_datetime(raw: str, formats: tuple[str, ...], kind: str) -> datetime:
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ParseError(f"not a {kind}: {raw!r}")


def _parse_int(raw: str, base: str) -> int:
    if not _INT_RE.fullmatch(raw):
        raise ParseError(f"not an integer: {raw!r}")
    value = int(raw)
    low, high = INT_RANGES[base]
    if not low <= value <= high:
        raise ParseError(f"{raw!r} out of {base} range")
    return value


def _parse_text(raw: str, base: str, args: tuple[int, ...]) -> str:
    if args:
        length = args[0]
        if base == "CHAR" and len(raw) != length:
            raise ParseError(f"{raw!r} is not exactly {length} characters")
        if base == "VARCHAR" and len(raw) > length:
            raise ParseError(f"{raw!r} longer than {length} characters")
    return raw


def parse_value(raw, column: Column):
    """Convert one raw value. Blank text becomes None; nullability is checked by the caller."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    base, args = column.base_type, column.type_args
    if base in ("VARCHAR", "CHAR", "TEXT"):
        return _parse_text(text, base, args)
    if base == "DECIMAL":
        precision, scale = (args + (0,))[:2] if args else (38, 0)
        return parse_decimal(text, scale=scale, precision=precision)
    if base in INT_RANGES:
        return _parse_int(text, base)
    if base == "DATE":
        return _parse_datetime(text, DATE_FORMATS, "date").date()
    if base == "TIMESTAMP":
        return _parse_datetime(text, TIMESTAMP_FORMATS, "timestamp")
    if base == "BOOLEAN":
        upper = text.upper()
        if upper in TRUE_VALUES:
            return True
        if upper in FALSE_VALUES:
            return False
        raise ParseError(f"not a boolean: {raw!r}")
    raise ParseError(f"unsupported type {column.type}")


def check_constraints(value, column: Column) -> None:
    """Nullability, allowed values and pattern for an already-typed value."""
    if value is None:
        if not column.nullable and not column.is_pending:
            raise ParseError("required value is missing")
        return
    if column.allowed and value not in column.allowed:
        raise ParseError(f"{value!r} not in allowed values {list(column.allowed)}")
    if column.pattern and not re.fullmatch(column.pattern, str(value)):
        raise ParseError(f"{value!r} does not match pattern {column.pattern}")


def to_date(value) -> date:
    """Date-key integers (YYYYMMDD) and dates both normalise to a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y%m%d").date()
