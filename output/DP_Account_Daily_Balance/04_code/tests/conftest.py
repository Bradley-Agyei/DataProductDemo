"""Fixture product for FR-07: two accounts x three days that pass every rule.

FR-01 to FR-06 are not built yet, so publish is tested on a hand-built frame in
the shape they will produce. A0000002 goes overdrawn on day 1.
"""
from datetime import date, datetime
from decimal import Decimal as D

import pandas as pd
import pytest

from src.account_daily_balance.run import publish

LOAD_TS = datetime(2026, 10, 8, 6, 0, 0)
DAYS = [date(2026, 9, 21), date(2026, 9, 22), date(2026, 9, 23)]

# account_id, member_id, status, opening day 1, [(credits, debits, count) per day]
ACCOUNTS = [
    ("A0000001", "M000001", "Open", D("500.00"), [(D("100.00"), D("0.00"), 1), (D("0.00"), D("50.00"), 1),
                                                   (D("0.00"), D("0.00"), 0)]),
    ("A0000002", "M000002", "Restricted", D("20.00"), [(D("0.00"), D("50.00"), 1), (D("40.00"), D("0.00"), 1),
                                                        (D("0.00"), D("0.00"), 0)]),
]


def make_product() -> pd.DataFrame:
    rows = []
    for account_id, member_id, status, opening, moves in ACCOUNTS:
        for day, (credits, debits, count) in zip(DAYS, moves):
            closing = opening + credits - debits
            rows.append({"balance_date": day, "account_id": account_id, "member_id": member_id,
                         "product_code": None, "account_status": status, "opening_balance": opening,
                         "total_credits": credits, "total_debits": debits, "closing_balance": closing,
                         "available_balance": None, "overdraft_flag": closing < 0,
                         "transaction_count": count, "pending_debits": D("0.00")})
            opening = closing
    return pd.DataFrame(rows, dtype=object)


def make_counted() -> pd.DataFrame:
    return pd.DataFrame({"account_id": ["A0000001", "A0000001", "A0000002", "A0000002"],
                         "signed_amount": [D("100.00"), D("-50.00"), D("-50.00"), D("40.00")]}, dtype=object)


def run_publish(tmp_path, product=None, counted=None, **kwargs):
    kwargs.setdefault("load_ts", LOAD_TS)
    kwargs.setdefault("db_path", tmp_path / "account_daily_balance.db")
    kwargs.setdefault("out_dir", tmp_path / "out")
    return publish(make_product() if product is None else product,
                   make_counted() if counted is None else counted, **kwargs)


@pytest.fixture(scope="session")
def result(tmp_path_factory):
    return run_publish(tmp_path_factory.mktemp("run"), batch_id="0b9d7f5e-6a43-4c1e-9a52-3f1d2c7e8a10")
