"""SCRUM-44 / FR-01: the transaction extract and its reference tables land unchanged in raw.

Comparisons use DataFrame.equals so a failure reports only True/False: the
Member extract holds PII and no value may reach the test output.
"""
import json
import sqlite3
import uuid

import pandas as pd
import pytest

from contracts.sources import SOURCES
from src.dp_framework.contract import SchemaError
from src.payment_transaction import config
from src.payment_transaction.raw import FR01_LOAD_COLUMNS
from tests.conftest import rewrite_header, run_build

EXPECTED_ROWS = {"Transaction.csv": 100, "Transaction_Type.csv": 10, "Channel.csv": 10, "Date.csv": 10,
                 "Branch.csv": 10, "Account.csv": 10, "Member.csv": 10}


def read_raw(db, name):
    with sqlite3.connect(db) as conn:
        return pd.read_sql_query(f'SELECT * FROM "raw_{name.lower()}"', conn)


def read_source(name):
    return pd.read_csv(config.SOURCE_DIR / f"{name}.csv", dtype=str, keep_default_na=False,
                       encoding="utf-8-sig")


def test_seven_sources_in_scope():
    assert sorted(config.SOURCE_FILES.values()) == sorted(EXPECTED_ROWS)


# AC: All 7 files land in raw with values unchanged (text)
@pytest.mark.parametrize("name", SOURCES)
def test_values_land_unchanged_as_text(result, name):
    landed = read_raw(result.db_path, name)
    source = read_source(name)
    assert list(landed.columns[:len(source.columns)]) == list(source.columns)
    assert landed[list(source.columns)].astype(object).equals(source.astype(object))


def test_raw_columns_are_untyped_text(result):
    with sqlite3.connect(result.db_path) as conn:
        types = {r[2] for r in conn.execute("PRAGMA table_info(raw_transaction)")
                 if r[1] not in FR01_LOAD_COLUMNS}
    assert types == {"TEXT"}


# AC: Row counts recorded: Transaction 100, others 10
def test_row_counts_recorded(result):
    assert result.row_counts == EXPECTED_ROWS
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["row_counts"] == EXPECTED_ROWS
    assert manifest["dp_batch_id"] == result.batch_id


@pytest.mark.parametrize("name", SOURCES)
def test_raw_table_row_count_matches_file(result, name):
    assert len(read_raw(result.db_path, name)) == EXPECTED_ROWS[f"{name}.csv"]


# AC: A missing or renamed header fails the run before publish
@pytest.mark.parametrize("change", ["renamed", "missing"])
def test_header_change_fails_before_anything_is_written(tmp_path, src_copy, change):
    header = SOURCES["Channel"].column_names
    header = [*header[:1], "channel_label", *header[2:]] if change == "renamed" else header[:-1]
    rewrite_header(src_copy / "Channel.csv", header)
    with pytest.raises(SchemaError, match="Channel.csv"):
        run_build(tmp_path, src_dir=src_copy)
    assert not (tmp_path / "payment_transaction.db").exists()
    assert not (tmp_path / "out").exists()


def test_missing_file_fails_before_anything_is_written(tmp_path, src_copy):
    (src_copy / "Branch.csv").unlink()
    with pytest.raises(SchemaError, match="Branch.csv"):
        run_build(tmp_path, src_dir=src_copy)
    assert not (tmp_path / "payment_transaction.db").exists()
    assert not (tmp_path / "out").exists()


# AC: Each raw row carries source_file, dp_load_ts, dp_batch_id
@pytest.mark.parametrize("name", SOURCES)
def test_rows_carry_load_columns(result, name):
    landed = read_raw(result.db_path, name)
    assert list(landed.columns[-3:]) == list(FR01_LOAD_COLUMNS)
    assert (landed["source_file"] == f"{name}.csv").all()
    assert (landed["dp_load_ts"] == "2026-10-08 06:00:00").all()
    assert (landed["dp_batch_id"] == result.batch_id).all()


def test_default_batch_id_is_a_uuid(tmp_path):
    res = run_build(tmp_path)
    assert str(uuid.UUID(res.batch_id)) == res.batch_id
    assert len(res.batch_id) <= 36


def test_rerun_replaces_raw_rows(tmp_path):
    run_build(tmp_path)
    run_build(tmp_path)
    assert len(read_raw(tmp_path / "payment_transaction.db", "Transaction")) == 100
