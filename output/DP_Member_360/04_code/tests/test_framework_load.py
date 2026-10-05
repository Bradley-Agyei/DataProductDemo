"""Warehouse loading primitives shared by every data product."""
import sqlite3
from datetime import date

import pandas as pd
import pytest

from src.dp_framework.contract import Column, Table
from src.dp_framework.load import Warehouse

SNAPSHOT = Table("snap", (
    Column("snapshot_date", "DATE", key="PK"),
    Column("item_id", "VARCHAR(10)", key="PK"),
    Column("status", "VARCHAR(10)"),
))


def frame(day, *items):
    return pd.DataFrame([{"snapshot_date": day, "item_id": i, "status": s} for i, s in items], dtype=object)


def rows(db):
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT snapshot_date, item_id, status FROM snap ORDER BY 1, 2").fetchall()


def test_replace_partition_is_idempotent_and_isolated(tmp_path):
    db = tmp_path / "w.db"
    d1, d2 = date(2026, 10, 4), date(2026, 10, 5)
    with Warehouse(db) as wh:
        wh.replace_partition(SNAPSHOT, frame(d1, ("a", "Open"), ("b", "Open")), "snapshot_date", d1)
        wh.replace_partition(SNAPSHOT, frame(d1, ("a", "Closed"), ("b", "Open")), "snapshot_date", d1)
        wh.replace_partition(SNAPSHOT, frame(d2, ("a", "Closed")), "snapshot_date", d2)
    assert rows(db) == [("2026-10-04", "a", "Closed"), ("2026-10-04", "b", "Open"), ("2026-10-05", "a", "Closed")]


def test_replace_partition_rejects_unknown_column(tmp_path):
    with Warehouse(tmp_path / "w.db") as wh, pytest.raises(KeyError):
        wh.replace_partition(SNAPSHOT, frame(date(2026, 10, 4)), "nope", 1)


def test_failed_partition_load_rolls_back(tmp_path):
    db = tmp_path / "w.db"
    d1 = date(2026, 10, 4)
    with Warehouse(db) as wh:
        wh.replace_partition(SNAPSHOT, frame(d1, ("a", "Open")), "snapshot_date", d1)
        with pytest.raises(sqlite3.IntegrityError):
            wh.replace_partition(SNAPSHOT, frame(d1, ("a", "Open"), ("a", "Dup")), "snapshot_date", d1)
    assert rows(db) == [("2026-10-04", "a", "Open")]
