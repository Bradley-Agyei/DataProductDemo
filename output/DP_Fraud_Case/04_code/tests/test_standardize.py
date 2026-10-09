"""Typed staging: every extract column matches its contract type; bad rows are rejected with a reason."""
import sqlite3
from datetime import date, datetime
from decimal import Decimal

from contracts.sources import FRAUD_CASE_EXTRACT
from tests.conftest import by_case, edit_extract, run_build

PY_TYPES = {"VARCHAR": str, "CHAR": str, "TEXT": str, "INT": int, "SMALLINT": int,
            "DECIMAL": Decimal, "DATE": date, "TIMESTAMP": datetime, "BOOLEAN": bool}


def staged(res):
    return res.staged["Fraud_Case_Extract"]


def test_all_13_columns_have_contract_types(result):
    assert len(FRAUD_CASE_EXTRACT.columns) == 13
    frame = staged(result)
    for col in FRAUD_CASE_EXTRACT.columns:
        values = [v for v in frame[col.name] if v is not None]
        expected = PY_TYPES[col.base_type]
        assert all(type(v) is expected for v in values), f"{col.name} not {expected.__name__}"


def test_staging_table_declares_contract_types(result):
    with sqlite3.connect(result.db_path) as conn:
        declared = {r[1]: r[2] for r in conn.execute("PRAGMA table_info(stg_fraud_case_extract)")}
    assert all(declared[c.name] == c.type for c in FRAUD_CASE_EXTRACT.columns)


def test_amounts_and_timestamps_parse(result):
    rows = by_case(staged(result))
    assert rows.loc["FC0000007", "suspected_loss_amount"] == Decimal("1060.33")
    assert rows.loc["FC0000002", "confirmed_loss_amount"] == Decimal("299.50")
    assert rows.loc["FC0000002", "case_close_ts"] == datetime(2026, 8, 4, 16, 0)


def test_blanks_become_null_only_where_allowed(result):
    row = by_case(staged(result)).loc["FC0000001"]
    assert row["resolution_code"] is None and row["case_close_ts"] is None


def test_sample_has_no_rejects(result):
    assert result.rejects.empty


def test_unparseable_amount_is_rejected(tmp_path, src_copy):
    edit_extract(src_copy, "$237.19 ,$0.00", "abc,$0.00")
    res = run_build(tmp_path, src_dir=src_copy)
    reject = res.rejects.iloc[0]
    assert (reject["row_key"], reject["column_name"], reject["raw_value"]) == ("FC0000001", "suspected_loss_amount", "abc")
    assert len(res.product) == 99


def test_malformed_member_id_is_rejected(tmp_path, src_copy):
    edit_extract(src_copy, "FC0000005,M000005,", "FC0000005,M5,")
    res = run_build(tmp_path, src_dir=src_copy)
    reject = res.rejects.iloc[0]
    assert (reject["row_key"], reject["column_name"]) == ("FC0000005", "member_id")


def test_value_outside_allowed_list_is_rejected(tmp_path, src_copy):
    edit_extract(src_copy, "Identity Review,Rules Engine,Escalated,Low,$648.76",
                 "Identity Review,Rules Engine,Escalated,Urgent,$648.76")
    res = run_build(tmp_path, src_dir=src_copy)
    assert res.rejects.iloc[0][["row_key", "column_name"]].tolist() == ["FC0000004", "priority"]


def test_duplicate_case_ids_are_rejected(tmp_path, src_copy):
    path = src_copy / "DP_Fraud_Case.csv"
    first_case = path.read_text(encoding="utf-8").splitlines()[1]
    path.write_text(path.read_text(encoding="utf-8") + first_case + "\n", encoding="utf-8")
    res = run_build(tmp_path, src_dir=src_copy)
    assert (res.rejects["row_key"] == "FC0000001").sum() == 2
    assert len(res.product) == 99
