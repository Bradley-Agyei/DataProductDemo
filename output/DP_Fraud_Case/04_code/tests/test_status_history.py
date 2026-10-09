"""Case status history: one snapshot per case per run date, idempotent per date, success only."""
import sqlite3
from datetime import date

import pandas as pd

from src.fraud_case import run as run_module
from tests.conftest import run_build


def snapshot_counts(db):
    with sqlite3.connect(db) as conn:
        return dict(conn.execute("SELECT snapshot_date, COUNT(*) FROM fraud_case_status_snapshot GROUP BY 1"))


def test_two_run_dates_build_history(tmp_path):
    run_build(tmp_path, as_of=date(2026, 10, 4))
    run_build(tmp_path, as_of=date(2026, 10, 5))
    assert snapshot_counts(tmp_path / "fraud_case.db") == {"2026-10-04": 100, "2026-10-05": 100}


def test_same_date_rerun_is_idempotent(tmp_path):
    run_build(tmp_path, batch_id="one")
    run_build(tmp_path, batch_id="two")
    assert snapshot_counts(tmp_path / "fraud_case.db") == {"2026-10-04": 100}
    with sqlite3.connect(tmp_path / "fraud_case.db") as conn:
        assert {r[0] for r in conn.execute("SELECT DISTINCT dp_batch_id FROM fraud_case_status_snapshot")} == {"two"}


def test_snapshot_columns(result):
    with sqlite3.connect(result.db_path) as conn:
        row = conn.execute("SELECT * FROM fraud_case_status_snapshot WHERE case_id = 'FC0000002'").fetchone()
    assert row == ("2026-10-04", "FC0000002", "Closed", "High", "Digital Fraud", "test-batch")


def test_blocked_run_writes_no_snapshot(tmp_path, monkeypatch):
    run_build(tmp_path, as_of=date(2026, 10, 4))
    real_build = run_module.build_fraud_case

    def duplicated(*args, **kwargs):
        product = real_build(*args, **kwargs)
        return pd.concat([product, product.head(1)], ignore_index=True)

    monkeypatch.setattr(run_module, "build_fraud_case", duplicated)
    res = run_build(tmp_path, as_of=date(2026, 10, 5))
    assert res.status == "BLOCKED"
    assert snapshot_counts(tmp_path / "fraud_case.db") == {"2026-10-04": 100}
