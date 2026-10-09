"""Raw layer: read source files exactly as received and stamp load metadata."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .contract import Column, SchemaError, Table

META_COLUMNS = (
    Column("src_file_name", "VARCHAR(255)", description="Source file the row came from."),
    Column("src_load_ts", "TIMESTAMP", description="When the file was read."),
    Column("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
)


def raw_table(table: Table) -> Table:
    """Raw layer keeps every source value as untyped text."""
    cols = tuple(Column(c.name, "TEXT", nullable=True) for c in table.columns)
    return Table(f"raw_{table.name.lower()}", cols + META_COLUMNS, grain=table.grain)


def staged_table(table: Table) -> Table:
    return Table(f"stg_{table.name.lower()}", table.columns + META_COLUMNS, grain=table.grain)


def read_source(path: Path, table: Table, batch_id: str, load_ts: datetime) -> pd.DataFrame:
    """Every value is read as text so nothing is silently coerced before standardization."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if list(df.columns) != table.column_names:
        raise SchemaError(f"{path.name}: expected columns {table.column_names}, got {list(df.columns)}")
    df = df.astype(object)
    return df.assign(src_file_name=path.name, src_load_ts=load_ts, dp_batch_id=batch_id)


def ingest_all(src_dir: Path, tables: dict[str, Table], file_names: dict[str, str],
               batch_id: str, load_ts: datetime) -> dict[str, pd.DataFrame]:
    src_dir = Path(src_dir)
    frames = {}
    for name, table in tables.items():
        path = src_dir / file_names[name]
        if not path.exists():
            raise SchemaError(f"missing source file: {path}")
        frames[name] = read_source(path, table, batch_id, load_ts)
    return frames
