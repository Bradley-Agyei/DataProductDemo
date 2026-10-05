"""DQ-01..DQ-14 for Fraud Case, declared on top of the framework rule factories."""
from __future__ import annotations

from datetime import date
from typing import Mapping

import pandas as pd

from contracts.fraud_case import FRAUD_CASE
from contracts.sources import FRAUD_CASE_EXTRACT
from src.dp_framework.dq import (BLOCK, REJECT, WARN, Rule, allowed_values, matches_pattern,
                                 required_present, unique_not_null)

from .config import Settings

EXTRACT = FRAUD_CASE_EXTRACT.name
PRODUCT = FRAUD_CASE.name


def _closed(df: pd.DataFrame) -> pd.Series:
    return df["case_status"] == "Closed"


def _lifecycle_incomplete(frames) -> pd.Series:
    df = frames[EXTRACT]
    has_close, has_resolution = df["case_close_ts"].notna(), df["resolution_code"].notna()
    closed = _closed(df)
    return (closed & ~(has_close & has_resolution)) | (~closed & (has_close | has_resolution))


def _closed_before_opened(frames) -> pd.Series:
    df = frames[EXTRACT]
    return pd.Series([c is not None and c < o for o, c in zip(df["case_open_ts"], df["case_close_ts"])],
                     index=df.index)


def _loss_out_of_range(frames) -> pd.Series:
    df = frames[EXTRACT]
    return pd.Series([s < 0 or c < 0 or c > s
                      for s, c in zip(df["suspected_loss_amount"], df["confirmed_loss_amount"])], index=df.index)


def _unconfirmed_with_loss(frames) -> pd.Series:
    df = frames[EXTRACT]
    unconfirmed = (df["resolution_code"] == "False Positive") | ~_closed(df)
    return unconfirmed & (df["confirmed_loss_amount"] != 0)


def _confirmed_without_loss(frames) -> pd.Series:
    df = frames[EXTRACT]
    return (df["resolution_code"] == "Confirmed Fraud") & (df["confirmed_loss_amount"] == 0)


def source_rules(as_of: date, settings: Settings) -> list[Rule]:
    def opened_after_run_date(frames) -> pd.Series:
        return frames[EXTRACT]["case_open_ts"].map(lambda ts: ts.date() > as_of)

    return [
        Rule("DQ-06", "Closed if and only if close time and resolution are present", EXTRACT, REJECT,
             _lifecycle_incomplete),
        Rule("DQ-07", "case_close_ts is not before case_open_ts", EXTRACT, REJECT, _closed_before_opened),
        Rule("DQ-08", "0 <= confirmed loss <= suspected loss", EXTRACT, REJECT, _loss_out_of_range),
        Rule("DQ-09", "False Positive and open cases have no confirmed loss", EXTRACT, WARN,
             _unconfirmed_with_loss),
        Rule("DQ-10", "Confirmed Fraud has a confirmed loss", EXTRACT, settings.confirmed_zero_loss_severity,
             _confirmed_without_loss),
        Rule("DQ-11", "case_open_ts is not after the run date", EXTRACT, REJECT, opened_after_run_date),
    ]


def _unexpected_queue(allowed: Mapping[str, tuple[str, ...]] | None):
    def check(frames) -> pd.Series:
        df = frames[PRODUCT]
        return pd.Series([t in allowed and q not in allowed[t]
                          for t, q in zip(df["case_type"], df["assigned_queue"])], index=df.index)
    return check


def product_rules(expected_cases: int, match_rate: float, settings: Settings) -> list[Rule]:
    allowed = settings.allowed_queues_by_case_type
    minimum = settings.min_member_match_rate

    def reconcile(frames):
        return abs(len(frames[PRODUCT]) - expected_cases)

    def member_missing(frames) -> pd.Series:
        return frames[PRODUCT]["member_found_flag"] != True  # noqa: E712 - object column of bools

    def match_rate_below_minimum(frames) -> int:
        return 0 if match_rate >= minimum else int(member_missing(frames).sum())

    return [
        unique_not_null("DQ-01", PRODUCT, "case_id", BLOCK),
        matches_pattern("DQ-02", FRAUD_CASE, BLOCK),
        required_present("DQ-03", FRAUD_CASE, BLOCK),
        allowed_values("DQ-04", FRAUD_CASE, BLOCK),
        Rule("DQ-05", "product row count equals source cases", PRODUCT, BLOCK, reconcile),
        Rule("DQ-12", "member_id found in member_360 (row kept, flagged)", PRODUCT, WARN, member_missing),
        Rule("DQ-13", "assigned_queue is allowed for the case_type (routing matrix)", PRODUCT, WARN,
             _unexpected_queue(allowed), applies=lambda frames: allowed is not None),
        Rule("DQ-14", f"member match rate {match_rate:.2%} (minimum {minimum:.2%})", PRODUCT, BLOCK,
             match_rate_below_minimum),
    ]
