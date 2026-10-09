from datetime import date
from decimal import Decimal
import re

import pandas as pd
import pytest

from contracts.sources import ACCOUNT, DATE, MEMBER
from src.account_daily_balance import config
from src.account_daily_balance.standardize import standardize_sources
from src.dp_framework.standardize import standardize

RAW_DIR = config.PROJECT_ROOT / "data" / "raw"
ACCOUNT_MAP_PATH = config.ACCOUNT_ID_MAP_PATH


def read_source(name, columns):
    return pd.read_csv(RAW_DIR / f"{name}.csv", usecols=columns, dtype=str,
                       keep_default_na=False, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def sample_result():
    raw = {
        "Account": read_source("Account", ACCOUNT.column_names),
        "Transaction": read_source("Transaction", [
            "transaction_id", "account_id", "member_id", "transaction_type_id", "channel_id",
            "branch_id", "date_key", "amount", "currency_code", "debit_credit_indicator",
            "transaction_status", "balance_after", "reference_number",
        ]),
        "Transaction_Type": read_source("Transaction_Type", [
            "transaction_type_id", "transaction_type_name", "debit_credit_indicator",
            "transaction_category",
        ]),
        "Product": read_source("Product", [
            "product_id", "product_name", "product_category", "currency_code", "monthly_fee",
            "interest_rate_pct", "product_status",
        ]),
        "Member": read_source("Member", MEMBER.column_names),
        "Date": read_source("Date", DATE.column_names),
    }
    mapping = pd.read_csv(ACCOUNT_MAP_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return standardize_sources(raw, mapping)


def test_valid_sample_standardizes_without_rejects(sample_result):
    typed, rejects = sample_result
    assert rejects.empty
    assert len(typed["Account"]) == 10
    assert len(typed["Transaction"]) == 100
    assert len(typed["Date"]) == 10
    assert typed["Account"]["account_id"].map(lambda value: bool(re.fullmatch(r"A\d{7}", value))).all()
    assert typed["Member"]["member_id"].map(lambda value: bool(re.fullmatch(r"M\d{6}", value))).all()
    assert typed["Account"]["account_id"].nunique() == 10
    assert isinstance(typed["Account"].iloc[0]["current_balance"], Decimal)
    assert isinstance(typed["Transaction"].iloc[0]["amount"], Decimal)
    assert isinstance(typed["Transaction"].iloc[0]["balance_after"], Decimal)
    assert isinstance(typed["Product"].iloc[0]["monthly_fee"], Decimal)
    assert isinstance(typed["Member"].iloc[0]["join_date"], date)
    assert isinstance(typed["Date"].iloc[0]["full_date"], date)
    assert isinstance(typed["Date"].iloc[0]["date_key"], int)
    assert isinstance(typed["Date"].iloc[0]["is_weekend"], bool)


def test_account_ids_map_to_canonical_values():
    raw = pd.DataFrame({"account_id": ["A00001"], "member_id": ["M0001"]})
    result, rejects = standardize_sources(
        {name: frame for name, frame in _minimal_sources().items()
         if name != "Account"} | {"Account": _account_rows(raw)},
        _mapping(),
    )
    assert rejects.empty
    assert result["Account"].iloc[0]["account_id"] == "A0000001"


def test_unmapped_account_is_rejected_as_dq08():
    raw = _minimal_sources()
    raw["Account"].loc[0, "account_id"] = "A99999"
    _, rejects = standardize_sources(raw, _mapping())
    reject = rejects[rejects["reason"] == "DQ-08"].iloc[0]
    assert reject["table_name"] == "Account"
    assert reject["column_name"] == "account_id"


def test_member_ids_are_left_padded_to_six_digits():
    raw = _minimal_sources()
    raw["Member"].loc[0, "member_id"] = "M0001"
    typed, rejects = standardize_sources(raw, _mapping())
    assert rejects.empty
    assert typed["Member"].iloc[0]["member_id"] == "M000001"


@pytest.mark.parametrize(("value", "expected"), [
    ("$1,225.35 ", Decimal("1225.35")),
    ("($199.78)", Decimal("-199.78")),
])
def test_accounting_amounts_parse_to_decimal(value, expected):
    typed, rejects = standardize(pd.DataFrame({"current_balance": [value]}),
                                 _single_column_table(ACCOUNT, "current_balance"))
    assert rejects.empty
    assert typed.iloc[0]["current_balance"] == expected
    assert isinstance(typed.iloc[0]["current_balance"], Decimal)


def test_dates_parse_to_date_values():
    typed, rejects = standardize(pd.DataFrame({"open_date": ["1/8/2019"]}),
                                 _single_column_table(ACCOUNT, "open_date"))
    assert rejects.empty
    assert typed.iloc[0]["open_date"] == date(2019, 1, 8)


def test_date_key_parses_as_integer():
    typed, rejects = standardize(pd.DataFrame({"date_key": ["20260921"]}),
                                 _single_column_table(DATE, "date_key"))
    assert rejects.empty
    assert typed.iloc[0]["date_key"] == 20260921
    assert isinstance(typed.iloc[0]["date_key"], int)


@pytest.mark.parametrize(("table", "column", "value"), [
    (ACCOUNT, "current_balance", "not-money"),
    (ACCOUNT, "open_date", "not-a-date"),
    (DATE, "date_key", "2026x921"),
])
def test_unparseable_values_are_rejected(table, column, value):
    _, rejects = standardize(pd.DataFrame({column: [value]}),
                             _single_column_table(table, column))
    assert len(rejects) == 1
    assert rejects.iloc[0]["column_name"] == column
    assert rejects.iloc[0]["reason"]


def test_duplicate_account_keys_are_rejected():
    raw = pd.DataFrame({"account_id": ["A0000001", "A0000001"]})
    typed, rejects = standardize(raw, _single_column_table(ACCOUNT, "account_id"))
    assert typed.empty
    assert len(rejects) == 2
    assert (rejects["reason"] == "duplicate primary key").all()


def test_duplicate_unique_keys_are_rejected():
    raw = _minimal_sources()
    raw["Transaction"] = pd.DataFrame([_transaction_row("TXN000001"), _transaction_row("TXN000002")])
    typed, rejects = standardize_sources(raw, _mapping())
    assert typed["Transaction"].empty
    assert len(rejects) == 2
    assert (rejects[rejects["table_name"] == "Transaction"]["reason"]
            == "duplicate unique key").all()


def _single_column_table(table, column):
    from src.dp_framework.contract import Table
    return Table(table.name, (table.column(column),))


def _mapping():
    return pd.DataFrame({
        "source_system": ["core_banking"],
        "source_account_id": ["A00001"],
        "account_id": ["A0000001"],
        "in_core_banking": ["TRUE"],
    })


def _account_rows(raw):
    return pd.DataFrame({
        "account_id": raw["account_id"],
        "member_id": raw["member_id"],
        "product_id": ["P001"],
        "branch_id": ["B001"],
        "account_type": ["Checking"],
        "open_date": ["1/8/2019"],
        "account_status": ["Open"],
        "current_balance": ["$500.00"],
        "currency_code": ["USD"],
    })


def _transaction_row(transaction_id):
    return {
        "transaction_id": transaction_id,
        "account_id": "A00001",
        "member_id": "M0001",
        "transaction_type_id": "TT01",
        "channel_id": "C01",
        "branch_id": "B001",
        "date_key": "20260921",
        "amount": "$2.00",
        "currency_code": "USD",
        "debit_credit_indicator": "Credit",
        "transaction_status": "Posted",
        "balance_after": "$5.00",
        "reference_number": "REF1",
    }


def _minimal_sources():
    return {
        "Account": _account_rows(pd.DataFrame({"account_id": ["A00001"], "member_id": ["M0001"]})),
        "Transaction": pd.DataFrame(columns=[
            "transaction_id", "account_id", "member_id", "transaction_type_id", "channel_id",
            "branch_id", "date_key", "amount", "currency_code", "debit_credit_indicator",
            "transaction_status", "balance_after", "reference_number",
        ]),
        "Transaction_Type": pd.DataFrame(columns=[
            "transaction_type_id", "transaction_type_name", "debit_credit_indicator",
            "transaction_category",
        ]),
        "Product": pd.DataFrame(columns=[
            "product_id", "product_name", "product_category", "currency_code", "monthly_fee",
            "interest_rate_pct", "product_status",
        ]),
        "Member": pd.DataFrame({
            "member_id": ["M0001"], "join_date": ["1/5/2018"], "state": ["NC"],
            "member_status": ["Active"], "member_segment": ["Retail"],
        }),
        "Date": pd.DataFrame({
            "date_key": ["20260921"], "full_date": ["9/21/2026"], "day_name": ["Monday"],
            "month_name": ["September"], "month_number": ["9"], "quarter_number": ["3"],
            "year_number": ["2026"], "is_weekend": ["FALSE"],
        }),
    }
