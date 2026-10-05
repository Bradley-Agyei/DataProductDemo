"""Typed staging: every source column matches its contract type; bad rows are rejected with a reason."""
import sqlite3
from datetime import date, datetime
from decimal import Decimal

import pytest

from contracts.sources import SOURCES
from tests.conftest import edit_csv, run_build

PY_TYPES = {"VARCHAR": str, "CHAR": str, "TEXT": str, "INT": int, "SMALLINT": int,
            "DECIMAL": Decimal, "DATE": date, "TIMESTAMP": datetime, "BOOLEAN": bool}


@pytest.mark.parametrize("name", SOURCES)
def test_staged_values_have_contract_types(result, name):
    frame = result.staged[name]
    for col in SOURCES[name].columns:
        values = [v for v in frame[col.name] if v is not None]
        assert values, f"{name}.{col.name} is empty"
        expected = PY_TYPES[col.base_type]
        assert all(type(v) is expected for v in values), f"{name}.{col.name} not {expected.__name__}"


@pytest.mark.parametrize("name", SOURCES)
def test_staging_tables_declare_contract_types(result, name):
    with sqlite3.connect(result.db_path) as conn:
        declared = {r[1]: r[2] for r in conn.execute(f'PRAGMA table_info("stg_{name.lower()}")')}
    for col in SOURCES[name].columns:
        assert declared[col.name] == col.type


def test_all_60_source_columns_are_typed():
    assert sum(len(t.columns) for t in SOURCES.values()) == 60


def test_negative_balances_in_parentheses(result):
    txn = result.staged["Transaction"].set_index("transaction_id")
    assert txn.loc["TXN000023", "balance_after"] == Decimal("-199.78")
    assert txn.loc["TXN000073", "balance_after"] == Decimal("-248.30")


def test_sample_sources_have_no_rejects(result):
    assert result.rejects.empty


def test_unparseable_value_is_rejected_with_reason(tmp_path, src_copy):
    edit_csv(src_copy / "Account.csv", "A00001,M0001,P001,B001,Checking,1/8/2019,Open,$500.00 ",
             "A00001,M0001,P001,B001,Checking,1/8/2019,Open,abc")
    res = run_build(tmp_path, src_dir=src_copy)
    reject = res.rejects[res.rejects["table_name"] == "Account"].iloc[0]
    assert (reject["row_key"], reject["column_name"], reject["raw_value"]) == ("A00001", "current_balance", "abc")
    assert "A00001" not in set(res.staged["Account"]["account_id"])


def test_value_outside_allowed_list_is_rejected(tmp_path, src_copy):
    edit_csv(src_copy / "Transaction.csv", "Credit,Posted,$515.00 ", "Credit,Settled,$515.00 ")
    res = run_build(tmp_path, src_dir=src_copy)
    reject = res.rejects[res.rejects["table_name"] == "Transaction"].iloc[0]
    assert (reject["row_key"], reject["column_name"]) == ("TXN000001", "transaction_status")


def test_duplicate_primary_key_rows_are_rejected(tmp_path, src_copy):
    # Duplicate the first member row as read from the file, so no member data is written into the test.
    path = src_copy / "Member.csv"
    first_member = path.read_text(encoding="utf-8").splitlines()[1]
    path.write_text(path.read_text(encoding="utf-8") + first_member + "\n", encoding="utf-8")
    res = run_build(tmp_path, src_dir=src_copy)
    dupes = res.rejects[(res.rejects["table_name"] == "Member") & (res.rejects["row_key"] == "M0001")]
    assert len(dupes) == 2
    assert len(res.staged["Member"]) == 9
