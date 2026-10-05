"""DQ-01..DQ-11 for Member 360, declared on top of the framework rule factories."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from contracts.member_360 import MEMBER_360
from contracts.sources import SOURCES
from src.dp_framework.dq import (BLOCK, REJECT, WARN, Rule, allowed_values, foreign_keys_resolve,
                                 matches_pattern, required_present, unique_not_null)

from .config import US_STATES

PRODUCT = MEMBER_360.name


def _debit_credit_mismatch(frames) -> pd.Series:
    txn, types = frames["Transaction"], frames["Transaction_Type"]
    expected = txn["transaction_type_id"].map(dict(zip(types["transaction_type_id"],
                                                       types["debit_credit_indicator"])))
    return txn["debit_credit_indicator"] != expected


def source_rules(mapped_account_ids: set[str]) -> list[Rule]:
    """Accounts are checked before Transaction so rejected accounts cascade to their transactions."""
    def unmapped_account(frames) -> pd.Series:
        return ~frames["Account"]["account_id"].isin(list(mapped_account_ids))

    return [
        Rule("DQ-11", "account_id is in the account ID mapping reference table", "Account", REJECT,
             unmapped_account),
        foreign_keys_resolve("DQ-09", SOURCES["Account"], REJECT),
        foreign_keys_resolve("DQ-09", SOURCES["Transaction"], REJECT),
        Rule("DQ-10", "debit_credit_indicator matches the transaction type", "Transaction", WARN,
             _debit_credit_mismatch),
    ]


def product_rules(as_of: date, load_ts: datetime, expected_members: int) -> list[Rule]:
    """Reconciliation (DQ-07) runs before the row-rejecting rules so it measures the build itself."""
    def future_join(frames):
        return frames[PRODUCT]["member_since_date"].map(lambda d: d is not None and d > as_of)

    def bad_state(frames):
        s = frames[PRODUCT]["home_state"]
        return s.notna() & ~s.isin(list(US_STATES))

    def reconcile(frames):
        return abs(len(frames[PRODUCT]) - expected_members)

    def update_after_load(frames):
        return frames[PRODUCT]["last_profile_update_ts"].map(lambda ts: ts is not None and ts > load_ts)

    return [
        unique_not_null("DQ-01", PRODUCT, "member_id", BLOCK),
        matches_pattern("DQ-02", MEMBER_360, BLOCK),
        required_present("DQ-03", MEMBER_360, BLOCK),
        allowed_values("DQ-04", MEMBER_360, BLOCK),
        Rule("DQ-07", "product row count equals distinct source members", PRODUCT, BLOCK, reconcile),
        Rule("DQ-05", "member_since_date is not after the run date", PRODUCT, REJECT, future_join),
        Rule("DQ-06", "home_state is a valid USPS code", PRODUCT, REJECT, bad_state),
        Rule("DQ-08", "last_profile_update_ts is not after load time", PRODUCT, WARN, update_after_load),
    ]
