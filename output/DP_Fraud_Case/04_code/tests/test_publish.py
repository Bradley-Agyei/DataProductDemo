"""Publishing: product table, CSV, data contract and DDL agree with the contract; DQ gate holds."""
import csv
import json
import sqlite3

import pandas as pd
import pytest

from contracts.fraud_case import FRAUD_CASE
from src.dp_framework.contract import ddl
from src.fraud_case import config
from src.fraud_case import run as run_module
from src.fraud_case.run import DDL_TABLES
from tests.conftest import run_build

BLOCKING = ["DQ-01", "DQ-02", "DQ-03", "DQ-04", "DQ-05"]


def test_all_cases_published(result):
    assert result.status == "SUCCESS"
    assert len(result.product) == 100 and result.product["case_id"].is_unique


@pytest.mark.parametrize("rule_id", BLOCKING)
def test_blocking_rules_pass(result, rule_id):
    assert result.dq_results.set_index("rule_id").loc[rule_id, "status"] == "Pass"


def test_every_rule_recorded(result):
    assert set(result.dq_results["rule_id"]) == {f"DQ-{n:02d}" for n in range(1, 15)}


def test_product_table_declares_contract_types(result):
    with sqlite3.connect(result.db_path) as conn:
        declared = [(r[1], r[2]) for r in conn.execute("PRAGMA table_info(fraud_case)")]
    assert declared == [(c.name, c.type) for c in FRAUD_CASE.columns]
    assert len(declared) == 23


def test_csv_starts_with_sample_columns(result):
    with open(config.SAMPLE_PRODUCT_CSV, newline="", encoding="utf-8-sig") as f:
        sample_header = next(csv.reader(f))
    with open(result.out_dir / "fraud_case.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0][:13] == sample_header
    assert rows[0][13:] == FRAUD_CASE.column_names[13:]
    assert len(rows) == 101


def test_csv_value_formats(result):
    with open(result.out_dir / "fraud_case.csv", newline="", encoding="utf-8") as f:
        row = next(r for r in csv.DictReader(f) if r["case_id"] == "FC0000002")
    assert row["case_open_ts"] == "2026-08-01 16:00:00"
    assert row["suspected_loss_amount"] == "374.38"
    assert row["is_closed"] == "TRUE" and row["days_to_close"] == "3.00"


def test_data_contract(result):
    contract = json.loads((result.out_dir / "data_contract.json").read_text(encoding="utf-8"))
    assert [(c["name"], c["type"]) for c in contract["columns"]] == [(c.name, c.type) for c in FRAUD_CASE.columns]
    assert contract["primary_key"] == ["case_id"]
    assert (result.out_dir / "data_contract.md").exists()


def test_contract_declares_eastern_time(result):
    contract = json.loads((result.out_dir / "data_contract.json").read_text(encoding="utf-8"))
    assert contract["timezone"] == "America/New_York"
    descriptions = {c["name"]: c["description"] for c in contract["columns"]}
    assert "ET" in descriptions["case_open_ts"] and "ET" in descriptions["case_close_ts"]
    with open(result.out_dir / "fraud_case.csv", newline="", encoding="utf-8") as f:
        row = next(r for r in csv.DictReader(f) if r["case_id"] == "FC0000001")
    assert row["case_open_ts"] == "2026-08-01 08:00:00"


def test_committed_ddl_matches_contracts():
    for i, table in enumerate(DDL_TABLES, 1):
        path = config.DDL_DIR / f"{i:02d}_{table.name}.sql"
        assert path.read_text(encoding="utf-8") == ddl(table), f"{path.name} is stale: run --write-ddl"


def test_blocking_failure_keeps_previous_product(tmp_path, monkeypatch):
    run_build(tmp_path)
    real_build = run_module.build_fraud_case

    def duplicated(*args, **kwargs):
        product = real_build(*args, **kwargs)
        return pd.concat([product, product.head(1)], ignore_index=True)

    monkeypatch.setattr(run_module, "build_fraud_case", duplicated)
    res = run_build(tmp_path, batch_id="bad-batch")
    assert res.status == "BLOCKED"
    assert res.dq_results.set_index("rule_id").loc["DQ-01", "status"] == "Fail"
    with sqlite3.connect(tmp_path / "fraud_case.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM fraud_case").fetchone()[0] == 100
        assert conn.execute("SELECT COUNT(*) FROM fraud_case WHERE dp_batch_id = 'bad-batch'").fetchone()[0] == 0


def test_rerun_is_idempotent(tmp_path):
    first = run_build(tmp_path, batch_id="one").product.drop(columns=["dp_batch_id"])
    second = run_build(tmp_path, batch_id="two").product.drop(columns=["dp_batch_id"])
    assert first.equals(second)


def test_run_log_reconciles(result):
    log = result.run_log.set_index("table_name")
    assert log.loc["stg_fraud_case_extract", ["rows_in", "rows_out"]].tolist() == [100, 100]
    assert log.loc["fraud_case", ["rows_in", "rows_out", "status"]].tolist() == [100, 100, "SUCCESS"]
