"""Raw layer: the extract lands unchanged, with load metadata, and reruns never duplicate."""
import sqlite3

import pytest

from src.dp_framework.contract import SchemaError
from tests.conftest import edit_extract, run_build


def scalar(db, sql):
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchone()


def test_raw_row_count_matches_file(result):
    assert scalar(result.db_path, "SELECT COUNT(*) FROM raw_fraud_case_extract")[0] == 100


def test_raw_rows_carry_load_metadata(result):
    row = scalar(result.db_path, "SELECT src_file_name, src_load_ts, dp_batch_id FROM raw_fraud_case_extract LIMIT 1")
    assert row == ("DP_Fraud_Case.csv", "2026-10-04 06:00:00", "test-batch")


def test_quoted_amounts_stay_in_one_column(result):
    value = scalar(result.db_path,
                   "SELECT suspected_loss_amount FROM raw_fraud_case_extract WHERE case_id = 'FC0000007'")[0]
    assert value == "$1,060.33 "


def test_rerun_does_not_duplicate_raw_rows(tmp_path):
    run_build(tmp_path)
    run_build(tmp_path)
    assert scalar(tmp_path / "fraud_case.db", "SELECT COUNT(*) FROM raw_fraud_case_extract")[0] == 100


def test_changed_header_fails_fast(tmp_path, src_copy):
    edit_extract(src_copy, "assigned_queue", "queue")
    with pytest.raises(SchemaError, match="DP_Fraud_Case.csv"):
        run_build(tmp_path, src_dir=src_copy)
