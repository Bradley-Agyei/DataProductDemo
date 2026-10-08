"""FR-01 (SCRUM-44): land the transaction extract and its reference tables unchanged in raw.

dp_framework reads every file as text and checks its header; this module renames
the framework's load columns to the names FR-01 specifies, loads the raw tables
and records a row count per file. Every file is read and checked before any
table is written, so a header change fails the run before anything is published.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.dp_framework.contract import Column, Table
from src.dp_framework.ingest import ingest_all
from src.dp_framework.load import Warehouse

FR01_LOAD_COLUMNS = ("source_file", "dp_load_ts", "dp_batch_id")
_RENAME = {"src_file_name": "source_file", "src_load_ts": "dp_load_ts"}
_LOAD_META = (
    Column("source_file", "VARCHAR(255)", description="Source file the row came from."),
    Column("dp_load_ts", "TIMESTAMP", description="When the file was read."),
    Column("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
)


def raw_table(table: Table) -> Table:
    """Every source value as untyped text, then the FR-01 load columns."""
    cols = tuple(Column(c.name, "TEXT", nullable=True) for c in table.columns)
    return Table(f"raw_{table.name.lower()}", cols + _LOAD_META, grain=table.grain)


def ingest_raw(src_dir: Path, sources: dict[str, Table], file_names: dict[str, str],
               batch_id: str, load_ts: datetime) -> dict[str, pd.DataFrame]:
    """Read and header-check all sources; raises SchemaError before anything is written."""
    frames = ingest_all(src_dir, sources, file_names, batch_id, load_ts)
    return {name: df.rename(columns=_RENAME) for name, df in frames.items()}


def land_raw(raw: dict[str, pd.DataFrame], sources: dict[str, Table], db_path: Path) -> None:
    with Warehouse(db_path) as wh:
        for name, df in raw.items():
            wh.replace(raw_table(sources[name]), df)


def row_counts(raw: dict[str, pd.DataFrame], file_names: dict[str, str]) -> dict[str, int]:
    return {file_names[name]: len(df) for name, df in raw.items()}


def write_manifest(out_dir: Path, batch_id: str, load_ts: datetime, counts: dict[str, int]) -> Path:
    """Counts only: the raw layer holds PII, so no row value is ever written here."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "raw_manifest.json"
    path.write_text(json.dumps({"dp_batch_id": batch_id, "dp_load_ts": load_ts.isoformat(sep=" "),
                                "row_counts": counts}, indent=2), encoding="utf-8")
    return path
