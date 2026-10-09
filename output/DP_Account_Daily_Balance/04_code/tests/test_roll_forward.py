"""SCRUM-40 / FR-04: balance roll-forward."""
from datetime import date, timedelta
from decimal import Decimal as D

import pandas as pd
import pytest

from src.account_daily_balance.dq_rules import PRODUCT, product_rules
from src.account_daily_balance.roll_forward import calendar_spine, roll_forward
from tests.sample_inputs import daily_totals, load_accounts, load_dates, load_sample, load_transactions

DAY1 = date(2026, 9, 21)
TOTAL_COLUMNS = ["account_id", "balance_date", "total_credits", "total_debits"]


def days(n):
    return pd.DataFrame({"full_date": [DAY1 + timedelta(d) for d in range(n)]}, dtype=object)


def accounts(*rows):
    """rows: (account_id, open_date, current_balance)"""
    return pd.DataFrame(rows, columns=["account_id", "open_date", "current_balance"], dtype=object)


def totals(*rows, columns=TOTAL_COLUMNS):
    """rows: (account_id, day offset, credits, debits, ...extras)"""
    rows = [(r[0], DAY1 + timedelta(r[1]), *r[2:]) for r in rows]
    return pd.DataFrame(rows, columns=columns, dtype=object)


def one_account(opening="500.00"):
    return accounts(("A0000001", DAY1, D(opening)))


def by_day(frame, account_id="A0000001"):
    return frame[frame["account_id"] == account_id].set_index("balance_date")


@pytest.fixture(scope="module")
def sample():
    return roll_forward(*load_sample())


# --- unit ---

def test_first_day_opens_at_current_balance():
    out = roll_forward(one_account(), days(1), totals())
    assert out.loc[0, "opening_balance"] == D("500.00")


def test_opening_equals_previous_closing():
    out = roll_forward(one_account(), days(3), totals(("A0000001", 0, D("100.00"), D("0.00")),
                                                      ("A0000001", 1, D("0.00"), D("30.00"))))
    assert list(out["opening_balance"]) == [D("500.00"), D("600.00"), D("570.00")]
    assert list(out["opening_balance"][1:]) == list(out["closing_balance"][:-1])


def test_closing_is_opening_plus_credits_minus_debits():
    out = roll_forward(one_account("1000.00"), days(1), totals(("A0000001", 0, D("250.00"), D("150.00"))))
    assert out.loc[0, "closing_balance"] == D("1100.00")


def test_day_without_activity_carries_balance():
    out = roll_forward(one_account(), days(3), totals(("A0000001", 0, D("100.00"), D("0.00"))))
    quiet = out.iloc[1:]
    assert (quiet["total_credits"] == D("0.00")).all() and (quiet["total_debits"] == D("0.00")).all()
    assert list(quiet["opening_balance"]) == list(quiet["closing_balance"]) == [D("600.00")] * 2


def test_account_not_open_has_no_rows_before_open_date():
    accts = accounts(("A0000001", DAY1, D("500.00")), ("A0000002", DAY1 + timedelta(2), D("10.00")))
    spine = calendar_spine(accts, days(3))
    assert len(spine) == 4
    assert list(by_day(spine, "A0000002").index) == [DAY1 + timedelta(2)]
    assert roll_forward(accts, days(3), totals()).query("account_id == 'A0000002'")["opening_balance"].tolist() == [D("10.00")]


def test_totals_outside_spine_raise():
    with pytest.raises(ValueError, match="not in the calendar spine"):
        roll_forward(one_account(), days(1), totals(("A0000001", 1, D("5.00"), D("0.00"))))


def test_missing_opening_balance_raises():
    with pytest.raises(ValueError, match="no current_balance"):
        roll_forward(accounts(("A0000001", DAY1, None)), days(1), totals())


def test_duplicate_totals_raise():
    row = ("A0000001", 0, D("1.00"), D("0.00"))
    with pytest.raises(ValueError, match="duplicate"):
        roll_forward(one_account(), days(1), totals(row, row))


def test_extra_total_columns_pass_through_zero_filled():
    cols = TOTAL_COLUMNS + ["transaction_count", "pending_debits"]
    out = roll_forward(one_account(), days(2), totals(("A0000001", 0, D("100.00"), D("0.00"), 5, D("10.00")),
                                                      columns=cols))
    assert list(out.columns[-2:]) == ["transaction_count", "pending_debits"]
    assert list(out["transaction_count"]) == [5, 0]
    assert list(out["pending_debits"]) == [D("10.00"), D("0.00")]


def test_negative_closing_allowed():
    out = roll_forward(one_account("100.00"), days(1), totals(("A0000001", 0, D("0.00"), D("150.00"))))
    assert out.loc[0, "closing_balance"] == D("-50.00")


# --- sample acceptance (Jira SCRUM-40) ---

# AC: one row per account per calendar day, 100 rows from the sample (10 x 10)
def test_sample_has_one_row_per_account_per_day(sample):
    assert len(sample) == 100
    assert not sample.duplicated(["account_id", "balance_date"]).any()
    assert sample.groupby("account_id").size().eq(10).all()


# AC: DQ-05 and DQ-06 pass on every row
@pytest.mark.parametrize("rule_id", ["DQ-05", "DQ-06"])
def test_sample_passes_dq05_and_dq06(sample, rule_id):
    rule = next(r for r in product_rules(pd.DataFrame(columns=["account_id", "signed_amount"]))
                if r.rule_id == rule_id)
    assert not rule.check({PRODUCT: sample}).any()


# AC: A0000001 opens 2026-09-21 at 500.00, closes 10,713.32; 2026-09-22 opens 10,713.32
def test_sample_a0000001_roll_forward(sample):
    a1 = by_day(sample)
    first = a1.loc[DAY1]
    assert (first["opening_balance"], first["total_credits"], first["total_debits"], first["closing_balance"]) == \
        (D("500.00"), D("10213.32"), D("0.00"), D("10713.32"))
    assert a1.loc[DAY1 + timedelta(1), "opening_balance"] == D("10713.32")
    assert (a1["closing_balance"] == D("10713.32")).all()


# AC: source balance_after is not used (Q3)
def test_balance_after_does_not_affect_output(sample):
    scrambled = load_transactions().assign(balance_after="$0.00")
    out = roll_forward(load_accounts(), load_dates(), daily_totals(scrambled))
    pd.testing.assert_frame_equal(out, sample)
