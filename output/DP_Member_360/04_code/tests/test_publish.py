"""Publishing: product table, CSV export, data contract and DDL all agree with the contract."""
import csv
import json
import sqlite3

from contracts.member_360 import MEMBER_360
from src.dp_framework.contract import ddl
from src.member_360 import config
from src.member_360.run import DDL_TABLES
from tests.conftest import run_build


def test_product_table_declares_contract_types(result):
    with sqlite3.connect(result.db_path) as conn:
        declared = [(r[1], r[2]) for r in conn.execute("PRAGMA table_info(member_360)")]
    assert declared == [(c.name, c.type) for c in MEMBER_360.columns]


def test_csv_matches_sample_product_shape(result):
    with open(config.SAMPLE_PRODUCT_CSV, newline="", encoding="utf-8-sig") as f:
        sample_header = next(csv.reader(f))
    with open(result.out_dir / "member_360.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0][:len(sample_header)] == sample_header
    assert rows[0][len(sample_header):] == ["dp_load_ts", "dp_batch_id"]
    assert len(rows) == 11


def test_csv_value_formats(result):
    with open(result.out_dir / "member_360.csv", newline="", encoding="utf-8") as f:
        row = next(r for r in csv.DictReader(f) if r["member_id"] == "M000001")
    assert row["member_since_date"] == "2018-01-05"
    assert row["dp_load_ts"] == "2026-10-04 06:00:00"
    assert row["age_band"] == ""


def test_data_contract_lists_every_column_with_type(result):
    contract = json.loads((result.out_dir / "data_contract.json").read_text(encoding="utf-8"))
    assert [(c["name"], c["type"]) for c in contract["columns"]] == [(c.name, c.type) for c in MEMBER_360.columns]
    assert contract["primary_key"] == ["member_id"]
    pending = [c["name"] for c in contract["columns"] if c["status"] == "pending"]
    assert len(pending) == 5
    assert (result.out_dir / "data_contract.md").exists()


def test_committed_ddl_matches_contracts():
    for i, table in enumerate(DDL_TABLES, 1):
        path = config.DDL_DIR / f"{i:02d}_{table.name}.sql"
        assert path.read_text(encoding="utf-8") == ddl(table), f"{path.name} is stale: run --write-ddl"


def test_rerun_is_idempotent(tmp_path):
    first = run_build(tmp_path, batch_id="one").product.drop(columns=["dp_batch_id"])
    second = run_build(tmp_path, batch_id="two").product.drop(columns=["dp_batch_id"])
    assert first.equals(second)
    with sqlite3.connect(tmp_path / "member_360.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM member_360").fetchone()[0] == 10
