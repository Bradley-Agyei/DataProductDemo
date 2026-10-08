"""SCRUM-43 / FR-07: publish with DQ gate, exceptions and data contract."""
import csv
import json
import sqlite3
from decimal import Decimal as D

import pandas as pd
import pytest

from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE
from src.account_daily_balance import config
from src.account_daily_balance.run import DDL_TABLES
from src.dp_framework.contract import ddl
from src.dp_framework.standardize import REJECT_COLUMNS
from tests.conftest import make_counted, make_product, run_publish

CRITICAL = ["DQ-01", "DQ-02", "DQ-03", "DQ-04", "DQ-05", "DQ-06", "DQ-07", "DQ-10"]


def product_rows(db):
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT COUNT(*), MIN(dp_batch_id) FROM account_daily_balance").fetchone()


def test_clean_input_publishes(result):
    assert result.status == "SUCCESS"
    assert len(result.product) == 6
    assert product_rows(result.db_path) == (6, result.batch_id)


@pytest.mark.parametrize("rule_id", CRITICAL)
def test_critical_rules_pass_on_clean_input(result, rule_id):
    row = result.dq_results.set_index("rule_id").loc[rule_id]
    assert (row["severity"], row["status"]) == ("block", "Pass")


# AC: CSV header starts with the 11 sample columns in sample order
def test_csv_header_starts_with_sample_columns(result):
    if config.SAMPLE_PRODUCT_CSV.exists():
        with open(config.SAMPLE_PRODUCT_CSV, newline="", encoding="utf-8-sig") as f:
            sample = next(csv.reader(f))
    else:
        sample = list(config.SAMPLE_COLUMNS)
    assert len(sample) == 11
    with open(result.out_dir / "account_daily_balance.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0][:11] == sample
    assert rows[0] == ACCOUNT_DAILY_BALANCE.column_names
    assert len(rows) == 7


def test_csv_value_formats(result):
    with open(result.out_dir / "account_daily_balance.csv", newline="", encoding="utf-8") as f:
        row = next(r for r in csv.DictReader(f) if r["account_id"] == "A0000002" and r["balance_date"] == "2026-09-21")
    assert (row["closing_balance"], row["overdraft_flag"], row["available_balance"]) == ("-30.00", "TRUE", "")


# AC: Critical DQ rules (DQ-01-07, DQ-10) block publish; previous product stays
def _break(rule_id):
    product, counted = make_product(), make_counted()
    if rule_id == "DQ-01":
        product = pd.concat([product, product.head(1)], ignore_index=True)
    elif rule_id == "DQ-02":
        product.loc[0, "account_id"] = "A00001"
    elif rule_id == "DQ-03":
        product.loc[0, "member_id"] = None
    elif rule_id == "DQ-04":
        product.loc[0, "account_status"] = "Closed"
    elif rule_id == "DQ-05":
        product.loc[0, "total_credits"] = D("99.00")
    elif rule_id == "DQ-06":
        product.loc[1, "opening_balance"] += D("1.00")
        product.loc[1, "closing_balance"] += D("1.00")
        product.loc[2, "opening_balance"] += D("1.00")
        product.loc[2, "closing_balance"] += D("1.00")
    elif rule_id == "DQ-07":
        counted.loc[0, "signed_amount"] = D("90.00")
    elif rule_id == "DQ-10":
        product.loc[3, "overdraft_flag"] = False
    return product, counted


@pytest.mark.parametrize("rule_id", CRITICAL)
def test_critical_failure_blocks_and_keeps_previous_product(tmp_path, rule_id):
    good = run_publish(tmp_path, batch_id="good")
    product, counted = _break(rule_id)
    bad = run_publish(tmp_path, product=product, counted=counted, batch_id="bad")
    assert bad.status == "BLOCKED"
    assert bad.dq_results.set_index("rule_id").loc[rule_id, "status"] == "Fail"
    assert product_rows(good.db_path) == (6, "good")
    with open(tmp_path / "out" / "account_daily_balance.csv", newline="", encoding="utf-8") as f:
        assert {r["dp_batch_id"] for r in csv.DictReader(f)} == {"good"}
    assert json.loads((tmp_path / "out" / "data_contract.json").read_text(encoding="utf-8"))["dp_batch_id"] == "good"
    assert bad.run_log.loc[0, "status"] == "BLOCKED" and bad.run_log.loc[0, "rows_out"] == 0


def test_dq07_catches_offsetting_credit_and_debit_errors(tmp_path):
    """Net movement still matches, but credits and debits each differ from source (PRD §10 DQ-07)."""
    counted = pd.concat([make_counted(), pd.DataFrame({"account_id": ["A0000001", "A0000001"],
                                                        "signed_amount": [D("25.00"), D("-25.00")]})],
                        ignore_index=True)
    res = run_publish(tmp_path, counted=counted)
    assert res.status == "BLOCKED"
    assert res.dq_results.set_index("rule_id").loc["DQ-07", ["status", "rows_failed"]].tolist() == ["Fail", 1]


def test_blocked_first_run_publishes_nothing(tmp_path):
    product, counted = _break("DQ-05")
    res = run_publish(tmp_path, product=product, counted=counted)
    assert res.status == "BLOCKED"
    assert not (tmp_path / "out" / "account_daily_balance.csv").exists()
    assert not (tmp_path / "out" / "data_contract.json").exists()


# AC: Exception report lists rejects and warnings with rule ID
def test_exception_report_lists_rejects_and_warnings_with_rule_id(tmp_path):
    product = make_product()
    product.loc[0, "available_balance"] = D("10000.00")
    upstream = pd.DataFrame([{"table_name": "stg_account", "row_key": "A00011", "column_name": "account_id",
                              "raw_value": "A00011", "reason": "DQ-08: account_id not in account_id_map"}],
                            columns=REJECT_COLUMNS)
    res = run_publish(tmp_path, product=product, upstream_rejects=upstream)
    assert res.status == "SUCCESS"
    got = res.exceptions[["exception_type", "rule_id", "row_key"]].values.tolist()
    assert ["REJECT", "DQ-08", "A00011"] in got
    assert ["WARN", "DQ-11", "2026-09-21|A0000001"] in got
    with open(tmp_path / "out" / "dq_exceptions.csv", newline="", encoding="utf-8") as f:
        report = list(csv.DictReader(f))
    assert {(r["exception_type"], r["rule_id"]) for r in report} == {("REJECT", "DQ-08"), ("WARN", "DQ-11")}
    assert all(r["rule_id"] for r in report)


# AC: DDL generated from the contract and kept in sync by a test
def test_committed_ddl_matches_contracts():
    for i, table in enumerate(DDL_TABLES, 1):
        path = config.DDL_DIR / f"{i:02d}_{table.name}.sql"
        assert path.read_text(encoding="utf-8") == ddl(table), f"{path.name} is stale: run --write-ddl"


def test_product_table_declares_contract_types(result):
    with sqlite3.connect(result.db_path) as conn:
        declared = [(r[1], r[2]) for r in conn.execute("PRAGMA table_info(account_daily_balance)")]
    assert declared == [(c.name, c.type) for c in ACCOUNT_DAILY_BALANCE.columns]
    assert len(declared) == 15


def test_data_contract(result):
    contract = json.loads((result.out_dir / "data_contract.json").read_text(encoding="utf-8"))
    assert [(c["name"], c["type"]) for c in contract["columns"]] == \
        [(c.name, c.type) for c in ACCOUNT_DAILY_BALANCE.columns]
    assert contract["primary_key"] == ["balance_date", "account_id"]
    pending = {c["name"] for c in contract["columns"] if c["status"] == "pending"}
    assert pending == {"product_code", "available_balance"}
    assert (result.out_dir / "data_contract.md").exists()


# AC: Rerun for the same date gives the same result (idempotent)
def test_rerun_is_idempotent(tmp_path):
    first = run_publish(tmp_path, batch_id="one").product.drop(columns=["dp_batch_id"])
    second = run_publish(tmp_path, batch_id="two").product.drop(columns=["dp_batch_id"])
    assert first.equals(second)
    assert product_rows(tmp_path / "account_daily_balance.db") == (6, "two")


# AC: No PII (no names, addresses, postal codes)
def test_contract_has_no_pii_columns():
    assert not [c for c in ACCOUNT_DAILY_BALANCE.column_names if config.is_pii_column(c)]


@pytest.mark.parametrize("name", ["first_name", "Last Name", "postal_code", "zip", "address"])
def test_pii_names_recognised(name):
    assert config.is_pii_column(name)


def test_pii_column_reaching_publish_is_masked_and_never_written(tmp_path):
    product = make_product().assign(first_name="should-not-appear", postal_code="should-not-appear")
    res = run_publish(tmp_path, product=product)
    assert res.status == "SUCCESS"
    assert (res.product[["first_name", "postal_code"]] == config.PII_MASK).all().all()
    with sqlite3.connect(res.db_path) as conn:
        columns = {r[1] for r in conn.execute("PRAGMA table_info(account_daily_balance)")}
    assert not [c for c in columns if config.is_pii_column(c)]
    text = (tmp_path / "out" / "account_daily_balance.csv").read_text(encoding="utf-8")
    assert "should-not-appear" not in text


def test_pii_reject_value_and_reason_are_masked(tmp_path):
    upstream = pd.DataFrame([
        {"table_name": "stg_member", "row_key": "M000099", "column_name": "postal_code",
         "raw_value": "should-not-appear", "reason": "'should-not-appear' is not exactly 5 characters"},
        {"table_name": "stg_member", "row_key": "M000098", "column_name": "first_name",
         "raw_value": "should-not-appear", "reason": "DQ-08: 'should-not-appear' failed"},
    ], columns=REJECT_COLUMNS)
    res = run_publish(tmp_path, upstream_rejects=upstream)
    with sqlite3.connect(res.db_path) as conn:
        rows = conn.execute("SELECT raw_value, reason FROM rejects").fetchall()
        report = conn.execute("SELECT rule_id, detail FROM dq_exceptions").fetchall()
    assert [r[0] for r in rows] == [config.PII_MASK, config.PII_MASK]
    for text in [*(r[1] for r in rows), *(d for _, d in report),
                 (tmp_path / "out" / "dq_exceptions.csv").read_text(encoding="utf-8")]:
        assert "should-not-appear" not in text
    assert sorted(rule for rule, _ in report) == ["DQ-08", "TYPE"]


def test_run_log_written(result):
    with open(result.out_dir / "run_log.csv", newline="", encoding="utf-8") as f:
        log = next(csv.DictReader(f))
    assert (log["table_name"], log["rows_in"], log["rows_out"], log["status"]) == \
        ("account_daily_balance", "6", "6", "SUCCESS")
