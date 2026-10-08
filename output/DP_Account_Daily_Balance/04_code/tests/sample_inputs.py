"""Test-only stand-in for FR-01 to FR-03 (SCRUM-37 to 39): sample inputs for the roll-forward.

Reads Account, Transaction and Date from data/raw (read-only; Member is never
opened), conforms account IDs via account_id_map and sums counted credits and
debits per account-day. Counts Posted only, the PRD's Q4 default. Delete this
once SCRUM-39 produces the daily totals.
"""
from __future__ import annotations

from decimal import Decimal

import pandas as pd

from src.account_daily_balance import config
from src.dp_framework.contract import Column
from src.dp_framework.types import parse_decimal, parse_value, to_date

RAW_DIR = config.PROJECT_ROOT / "data" / "raw"
ACCOUNT_MAP = config.PROJECT_ROOT / "data" / "reference" / "account_id_map.csv"
COUNTED_STATUSES = ("Posted",)
KEY = ["account_id", "balance_date"]
ZERO = Decimal("0.00")
_DATE = Column("date", "DATE")


def _read(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _amount(raw: str) -> Decimal:
    return parse_decimal(raw, scale=2, precision=15)


def _conform(source_ids: pd.Series) -> pd.Series:
    """Core-banking account ID (A00001) -> canonical ID (A0000001)."""
    ref = _read(ACCOUNT_MAP)
    ref = ref[ref["source_system"] == "core_banking"]
    ids = source_ids.map(dict(zip(ref["source_account_id"], ref["account_id"])))
    if ids.isna().any():
        raise ValueError(f"unmapped account IDs: {sorted(set(source_ids[ids.isna()]))}")
    return ids


def load_accounts() -> pd.DataFrame:
    raw = _read(RAW_DIR / "Account.csv")
    return pd.DataFrame({"account_id": _conform(raw["account_id"]),
                         "open_date": raw["open_date"].map(lambda v: parse_value(v, _DATE)),
                         "current_balance": raw["current_balance"].map(_amount)}, dtype=object)


def load_dates() -> pd.DataFrame:
    return pd.DataFrame({"full_date": _read(RAW_DIR / "Date.csv")["date_key"].map(to_date)}, dtype=object)


def load_transactions() -> pd.DataFrame:
    """Transaction.csv as received, all text."""
    return _read(RAW_DIR / "Transaction.csv")


def daily_totals(transactions: pd.DataFrame, counted_statuses=COUNTED_STATUSES) -> pd.DataFrame:
    """account_id, balance_date, total_credits, total_debits, transaction_count per account-day.
    Credits and debits are summed separately, never netted."""
    counted = transactions[transactions["transaction_status"].isin(counted_statuses)]
    side = counted["debit_credit_indicator"].str.strip()
    if not side.isin(["Credit", "Debit"]).all():
        raise ValueError(f"unknown debit_credit_indicator: {sorted(set(side) - {'Credit', 'Debit'})}")
    amount = counted["amount"].map(_amount)
    frame = pd.DataFrame({"account_id": _conform(counted["account_id"]),
                          "balance_date": counted["date_key"].map(to_date),
                          "total_credits": amount.where(side == "Credit", ZERO),
                          "total_debits": amount.where(side == "Debit", ZERO)}, dtype=object)
    rows = []
    for (account_id, day), group in frame.groupby(KEY, sort=True):
        rows.append({"account_id": account_id, "balance_date": day,
                     "total_credits": sum(group["total_credits"], ZERO),
                     "total_debits": sum(group["total_debits"], ZERO),
                     "transaction_count": len(group)})
    return pd.DataFrame(rows, columns=[*KEY, "total_credits", "total_debits", "transaction_count"], dtype=object)


def load_sample() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_accounts(), load_dates(), daily_totals(load_transactions())
