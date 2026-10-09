"""Product DQ rules for Account Daily Balance (PRD §10), on top of the framework rule factories.

Critical (block publish): DQ-01 to DQ-07 and DQ-10. DQ-11 is a warning.
DQ-08/09 are reject rules owned by FR-02/FR-03, DQ-12/13 warnings by FR-05/FR-06;
they reach the exception report through the rejects and warnings passed to publish.
"""
from __future__ import annotations

import pandas as pd

from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE
from src.dp_framework.dq import BLOCK, WARN, Rule, allowed_values, matches_pattern, required_present

from . import config

PRODUCT = ACCOUNT_DAILY_BALANCE.name
KEY = ["account_id", "balance_date"]


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(object).map(lambda v: None if v is None else float(v)), errors="coerce")


def _key_not_unique(frames) -> pd.Series:
    df = frames[PRODUCT]
    return df[KEY].isna().any(axis=1) | df.duplicated(KEY, keep=False)


def _closing_does_not_add_up(frames) -> pd.Series:
    df = frames[PRODUCT]
    expected = _num(df["opening_balance"]) + _num(df["total_credits"]) - _num(df["total_debits"])
    return (expected - _num(df["closing_balance"])).abs().gt(config.AMOUNT_TOLERANCE)


def _opening_breaks_chain(frames) -> pd.Series:
    df = frames[PRODUCT]
    ordered = df.sort_values(KEY)
    prior_close = _num(ordered["closing_balance"]).groupby(ordered["account_id"]).shift(1)
    broken = prior_close.notna() & (_num(ordered["opening_balance"]) - prior_close).abs().gt(config.AMOUNT_TOLERANCE)
    return broken.reindex(df.index)


def _overdraft_flag_wrong(frames) -> pd.Series:
    df = frames[PRODUCT]
    flagged = df["overdraft_flag"].astype(object).map(lambda v: v is not None and v == True)  # noqa: E712
    return flagged != _num(df["closing_balance"]).lt(0)


def _available_above_closing(frames) -> pd.Series:
    df = frames[PRODUCT]
    available = _num(df["available_balance"])
    return available.notna() & available.gt(_num(df["closing_balance"]) + config.AMOUNT_TOLERANCE)


def _reconciliation_breaks(counted: pd.DataFrame):
    """Accounts whose credits or debits differ from their counted source transactions (PRD §10 DQ-07).

    Credits and debits are reconciled separately, so offsetting errors cannot net to zero.
    """
    def check(frames) -> int:
        df = frames[PRODUCT]
        signed = _num(counted["signed_amount"])
        source = pd.DataFrame({"credits": signed.clip(lower=0), "debits": (-signed).clip(lower=0),
                               "account_id": counted["account_id"]}).groupby("account_id").sum()
        product = pd.DataFrame({"credits": _num(df["total_credits"]), "debits": _num(df["total_debits"]),
                                "account_id": df["account_id"]}).groupby("account_id").sum()
        diff = product.sub(source, fill_value=0).abs()
        return int(diff.gt(config.AMOUNT_TOLERANCE).any(axis=1).sum())
    return check


def product_rules(counted_transactions: pd.DataFrame) -> list[Rule]:
    """`counted_transactions`: account_id, signed_amount (credit +, debit -) for every counted transaction."""
    return [
        Rule("DQ-01", "account_id + balance_date is unique and not null", PRODUCT, BLOCK, _key_not_unique),
        matches_pattern("DQ-02", ACCOUNT_DAILY_BALANCE, BLOCK),
        required_present("DQ-03", ACCOUNT_DAILY_BALANCE, BLOCK),
        allowed_values("DQ-04", ACCOUNT_DAILY_BALANCE, BLOCK),
        Rule("DQ-05", "closing = opening + credits - debits", PRODUCT, BLOCK, _closing_does_not_add_up),
        Rule("DQ-06", "opening = previous day's closing", PRODUCT, BLOCK, _opening_breaks_chain),
        Rule("DQ-07", "credits and debits each reconcile to counted source transactions per account", PRODUCT, BLOCK,
             _reconciliation_breaks(counted_transactions)),
        Rule("DQ-10", "overdraft_flag = (closing_balance < 0)", PRODUCT, BLOCK, _overdraft_flag_wrong),
        Rule("DQ-11", "available_balance <= closing_balance", PRODUCT, WARN, _available_above_closing),
    ]
