"""Raw layer: sources land unchanged, with load metadata, and reruns never duplicate."""
import sqlite3

import pytest

from src.dp_framework.contract import SchemaError
from tests.conftest import edit_csv, run_build

EXPECTED_ROWS = {"account": 10, "branch": 10, "channel": 10, "date": 10, "member": 10,
                 "product": 10, "transaction": 100, "transaction_type": 10}


def count(db, table):
    with sqlite3.connect(db) as conn:
        return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


@pytest.mark.parametrize("table, rows", EXPECTED_ROWS.items())
def test_raw_row_counts_match_files(result, table, rows):
    assert count(result.db_path, f"raw_{table}") == rows


def test_raw_rows_carry_load_metadata(result):
    with sqlite3.connect(result.db_path) as conn:
        row = conn.execute(
            "SELECT src_file_name, src_load_ts, dp_batch_id FROM raw_account LIMIT 1").fetchone()
    assert row == ("Account.csv", "2026-10-04 06:00:00", "test-batch")


def test_quoted_values_with_commas_stay_in_one_column(result):
    with sqlite3.connect(result.db_path) as conn:
        value = conn.execute(
            "SELECT current_balance FROM raw_account WHERE account_id = 'A00002'").fetchone()[0]
    assert value == "$1,225.35 "


def test_rerun_does_not_duplicate_raw_rows(tmp_path):
    run_build(tmp_path)
    run_build(tmp_path)
    assert count(tmp_path / "member_360.db", "raw_transaction") == 100


def test_unexpected_header_fails_fast(tmp_path, src_copy):
    edit_csv(src_copy / "Branch.csv", "time_zone", "tz")
    with pytest.raises(SchemaError, match="Branch.csv"):
        run_build(tmp_path, src_dir=src_copy)
