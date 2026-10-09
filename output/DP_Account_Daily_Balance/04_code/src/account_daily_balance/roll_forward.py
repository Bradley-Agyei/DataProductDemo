"""FR-04 (SCRUM-40): balance roll-forward, one row per account per calendar day.

    calendar spine -> join daily totals -> chain opening and closing per account

The spine is every Date row x every account open on that day, so days without
activity carry the balance (Q7). Day 1 opens at config.FIRST_DAY_OPENING_COLUMN
(Q2); every later day opens at the previous closing (DQ-06), and closing is
opening + credits - debits (DQ-05). Only daily totals come in, never
transactions, so Transaction.balance_after cannot reach the balances (Q3).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from . import config

KEY = ["account_id", "balance_date"]
TOTALS = ["total_credits", "total_debits"]
CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def _cents(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def calendar_spine(accounts: pd.DataFrame, dates: pd.DataFrame) -> pd.DataFrame:
    """account_id x balance_date for every Date row on or after the account's open_date."""
    spine = accounts[["account_id", "open_date"]].merge(
        dates[["full_date"]].rename(columns={"full_date": "balance_date"}), how="cross")
    spine = spine[spine["open_date"] <= spine["balance_date"]]
    return spine[KEY].sort_values(KEY).reset_index(drop=True)


def roll_forward(accounts: pd.DataFrame, dates: pd.DataFrame, daily_totals: pd.DataFrame) -> pd.DataFrame:
    """`accounts`: account_id, open_date and the opening column. `daily_totals`: one row per
    account-day with activity, with total_credits and total_debits; any other column (such as
    transaction_count) passes through and is 0 on days without activity."""
    if accounts["account_id"].duplicated().any():
        raise ValueError("accounts has duplicate account_id")
    if daily_totals.duplicated(KEY).any():
        raise ValueError("daily_totals has duplicate account_id + balance_date")

    spine = calendar_spine(accounts, dates)
    outside = set(zip(*(daily_totals[k] for k in KEY))) - set(zip(*(spine[k] for k in KEY)))
    if outside:
        # Dropping them would lose counted activity and break DQ-07 reconciliation.
        raise ValueError(f"{len(outside)} daily_totals rows are not in the calendar spine: {sorted(outside)[:5]}")

    openings = accounts.set_index("account_id")[config.FIRST_DAY_OPENING_COLUMN]
    missing = sorted(a for a in spine["account_id"].unique() if pd.isna(openings[a]))
    if missing:
        raise ValueError(f"no {config.FIRST_DAY_OPENING_COLUMN} for {missing}")

    extras = [c for c in daily_totals.columns if c not in KEY + TOTALS]
    rows = spine.merge(daily_totals, on=KEY, how="left")
    for col in TOTALS:
        rows[col] = rows[col].map(lambda v: ZERO if pd.isna(v) else _cents(v)).astype(object)
    for col in extras:
        zero = ZERO if any(isinstance(v, Decimal) for v in rows[col].dropna()) else 0
        rows[col] = rows[col].map(lambda v, z=zero: z if pd.isna(v) else v).astype(object)

    # The spine is sorted by account then day, so each account's days are contiguous.
    opening, closing, account, balance = [], [], None, None
    for account_id, credits, debits in zip(rows["account_id"], rows["total_credits"], rows["total_debits"]):
        if account_id != account:
            account, balance = account_id, _cents(openings[account_id])
        opening.append(balance)
        balance = _cents(balance + credits - debits)
        closing.append(balance)
    rows["opening_balance"] = pd.Series(opening, index=rows.index, dtype=object)
    rows["closing_balance"] = pd.Series(closing, index=rows.index, dtype=object)

    return rows[["balance_date", "account_id", "opening_balance", *TOTALS, "closing_balance", *extras]]
