"""SCRUM-37 / FR-01: the core banking extracts land unchanged in raw.

PII columns (Member names, city and postal code) are header-checked but not landed
(CLAUDE.md). Tests never print a value and compare with DataFrame.equals so a
failure reports only True/False.
"""
import json
import shutil
import sqlite3
import uuid
from datetime import datetime

import pandas as pd
import pytest

from contracts.sources import SOURCES
from src.dp_framework.contract import SchemaError
from src.account_daily_balance import config
from src.account_daily_balance.raw import FR01_LOAD_COLUMNS, build, pii_columns

LOAD_TS = datetime(2026, 10, 8, 6, 0, 0)

EXPECTED_ROWS = {"Account.csv": 10, "Transaction.csv": 100, "Transaction_Type.csv": 10,
                 "Product.csv": 10, "Member.csv": 10, "Date.csv": 10}


def run_build(tmp_path, src_dir=config.SOURCE_DIR, **kwargs):
    kwargs.setdefault("load_ts", LOAD_TS)
    kwargs.setdefault("db_path", tmp_path / "account_daily_balance.db")
    kwargs.setdefault("out_dir", tmp_path / "out")
    return build(src_dir=src_dir, **kwargs)


def rewrite_header(path, header):
    """Replace only the header line; data rows are left as they are."""
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    lines[0] = ",".join(header) + "\n"
    path.write_text("".join(lines), encoding="utf-8")


@pytest.fixture(scope="module")
def raw_result(tmp_path_factory):
    """One build on the real sample sources, shared by read-only tests."""
    return run_build(tmp_path_factory.mktemp("run"), batch_id="0b9d7f5e-6a43-4c1e-9a52-3f1d2c7e8a10")


@pytest.fixture
def src_copy(tmp_path):
    """Writable copy of the sources for tests that change a header."""
    target = tmp_path / "src"
    shutil.copytree(config.SOURCE_DIR, target)
    return target


def read_raw(db, name):
    with sqlite3.connect(db) as conn:
        return pd.read_sql_query(f'SELECT * FROM "raw_{name.lower()}"', conn)


def read_source(name):
    return pd.read_csv(config.SOURCE_DIR / f"{name}.csv", dtype=str, keep_default_na=False,
                       encoding="utf-8-sig")


def test_six_sources_in_scope():
    assert sorted(config.SOURCE_FILES.values()) == sorted(EXPECTED_ROWS)


# AC: All 6 files land in raw with values unchanged (text); PII columns are not landed
@pytest.mark.parametrize("name", SOURCES)
def test_values_land_unchanged_as_text(raw_result, name):
    landed = read_raw(raw_result.db_path, name)
    source = read_source(name)
    kept = [c for c in source.columns if c not in pii_columns(SOURCES).get(name, ())]
    assert list(landed.columns[:len(kept)]) == kept
    assert landed[kept].astype(object).equals(source[kept].astype(object))


def test_pii_columns_are_not_landed(raw_result):
    dropped = pii_columns(SOURCES)
    assert dropped == {"Member": ("first_name", "last_name", "city", "postal_code")}
    landed = read_raw(raw_result.db_path, "Member")
    assert not set(dropped["Member"]) & set(landed.columns)
    assert len(landed) == EXPECTED_ROWS["Member.csv"]
    manifest_text = raw_result.manifest_path.read_text(encoding="utf-8")
    assert not any(c in manifest_text for c in dropped["Member"])
    assert json.loads(manifest_text)["pii_columns_dropped"] == {"Member.csv": 4}


def test_renamed_pii_column_still_fails_the_header_check(tmp_path, src_copy):
    header = [("given_name" if c == "first_name" else c) for c in SOURCES["Member"].column_names]
    rewrite_header(src_copy / "Member.csv", header)
    with pytest.raises(SchemaError, match="Member.csv"):
        run_build(tmp_path, src_dir=src_copy)
    assert not (tmp_path / "account_daily_balance.db").exists()


def test_raw_columns_are_untyped_text(raw_result):
    with sqlite3.connect(raw_result.db_path) as conn:
        types = {r[2] for r in conn.execute("PRAGMA table_info(raw_transaction)")
                 if r[1] not in FR01_LOAD_COLUMNS}
    assert types == {"TEXT"}


# AC: Row counts recorded: Account 10, Transaction 100, others 10
def test_row_counts_recorded(raw_result):
    assert raw_result.row_counts == EXPECTED_ROWS
    manifest = json.loads(raw_result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["row_counts"] == EXPECTED_ROWS
    assert manifest["dp_batch_id"] == raw_result.batch_id


@pytest.mark.parametrize("name", SOURCES)
def test_raw_table_row_count_matches_file(raw_result, name):
    assert len(read_raw(raw_result.db_path, name)) == EXPECTED_ROWS[f"{name}.csv"]


# AC: A missing or renamed header fails the run before publish
@pytest.mark.parametrize("change", ["renamed", "missing"])
def test_header_change_fails_before_anything_is_written(tmp_path, src_copy, change):
    header = SOURCES["Product"].column_names
    header = [*header[:1], "product_label", *header[2:]] if change == "renamed" else header[:-1]
    rewrite_header(src_copy / "Product.csv", header)
    with pytest.raises(SchemaError, match="Product.csv"):
        run_build(tmp_path, src_dir=src_copy)
    assert not (tmp_path / "account_daily_balance.db").exists()
    assert not (tmp_path / "out").exists()


def test_missing_file_fails_before_anything_is_written(tmp_path, src_copy):
    (src_copy / "Date.csv").unlink()
    with pytest.raises(SchemaError, match="Date.csv"):
        run_build(tmp_path, src_dir=src_copy)
    assert not (tmp_path / "account_daily_balance.db").exists()
    assert not (tmp_path / "out").exists()


# AC: Each raw row carries source_file, dp_load_ts, dp_batch_id
@pytest.mark.parametrize("name", SOURCES)
def test_rows_carry_load_columns(raw_result, name):
    landed = read_raw(raw_result.db_path, name)
    assert list(landed.columns[-3:]) == list(FR01_LOAD_COLUMNS)
    assert (landed["source_file"] == f"{name}.csv").all()
    assert (landed["dp_load_ts"] == "2026-10-08 06:00:00").all()
    assert (landed["dp_batch_id"] == raw_result.batch_id).all()


def test_default_batch_id_is_a_uuid(tmp_path):
    res = run_build(tmp_path)
    assert str(uuid.UUID(res.batch_id)) == res.batch_id
    assert len(res.batch_id) == 36


def test_rerun_replaces_raw_rows(tmp_path):
    run_build(tmp_path)
    run_build(tmp_path)
    assert len(read_raw(tmp_path / "account_daily_balance.db", "Transaction")) == 100
