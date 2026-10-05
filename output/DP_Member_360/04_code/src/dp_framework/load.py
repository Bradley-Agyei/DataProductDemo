"""SQLite warehouse stand-in: atomic full rebuilds and append-only history tables."""
from __future__ import annotations

import math
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .contract import Table, ddl


def to_sql_value(value):
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return int(value)
    return value


class Warehouse:
    def __init__(self, path: Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Autocommit mode so DDL participates in explicit transactions.
        self.conn = sqlite3.connect(path, isolation_level=None)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self.conn.close()

    @contextmanager
    def _transaction(self):
        self.conn.execute("BEGIN")
        try:
            yield
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        self.conn.execute("COMMIT")

    def replace(self, table: Table, df: pd.DataFrame) -> None:
        """Drop, recreate and reload in one transaction: readers never see a half-built table."""
        with self._transaction():
            self.conn.execute(f'DROP TABLE IF EXISTS "{table.name}"')
            self.conn.execute(ddl(table))
            self._insert(table, df)

    def append(self, table: Table, df: pd.DataFrame) -> None:
        with self._transaction():
            self._create_if_missing(table)
            self._insert(table, df)

    def replace_partition(self, table: Table, df: pd.DataFrame, column: str, value) -> None:
        """Swap one partition (e.g. a snapshot date) atomically; other partitions are untouched."""
        if column not in table.column_names:
            raise KeyError(f"{table.name} has no column {column}")
        with self._transaction():
            self._create_if_missing(table)
            self.conn.execute(f'DELETE FROM "{table.name}" WHERE {column} = ?', (to_sql_value(value),))
            self._insert(table, df)

    def _create_if_missing(self, table: Table) -> None:
        self.conn.execute(ddl(table).replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1))

    def _insert(self, table: Table, df: pd.DataFrame) -> None:
        if df.empty:
            return
        cols = table.column_names
        sql = f'INSERT INTO "{table.name}" ({", ".join(cols)}) VALUES ({", ".join("?" * len(cols))})'
        rows = [tuple(to_sql_value(r[c]) for c in cols) for r in df[cols].to_dict("records")]
        self.conn.executemany(sql, rows)
