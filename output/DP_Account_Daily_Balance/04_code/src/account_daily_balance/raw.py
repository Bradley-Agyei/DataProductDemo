"""FR-01 (SCRUM-37): land the core banking extracts in raw.

dp_framework reads every file as text and checks its full header; this module
drops every PII column (CLAUDE.md: PII never leaves data/raw; columns are
found with config.is_pii_column, the same rule FR-07 applies), renames the
framework's load columns to the names FR-01 specifies, loads the raw tables and
records a row count per file. Every file is read and checked before any table
is written, so a header change fails the run before anything is published.
"""
from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from contracts.sources import SOURCES
from src.account_daily_balance import config
from src.dp_framework.contract import Column, Table
from src.dp_framework.ingest import ingest_all
from src.dp_framework.load import Warehouse

# PRD section 5.5 types these as PII ("not published") although the repo-wide name list
# (config.is_pii_column) has no entry for them. Kept here so FR-07's PII rule is untouched.
PRD_PII_COLUMNS = {"Member": ("city",)}

FR01_LOAD_COLUMNS = ("source_file", "dp_load_ts", "dp_batch_id")
_RENAME = {"src_file_name": "source_file", "src_load_ts": "dp_load_ts"}
_LOAD_META = (
    Column("source_file", "VARCHAR(255)", description="Source file the row came from."),
    Column("dp_load_ts", "TIMESTAMP", description="When the file was read."),
    Column("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
)


def _is_pii(table_name: str, column: str) -> bool:
    return config.is_pii_column(column) or column in PRD_PII_COLUMNS.get(table_name, ())


def raw_table(table: Table) -> Table:
    """Every non-PII source column as untyped text, then the FR-01 load columns."""
    cols = tuple(Column(c.name, "TEXT", nullable=True) for c in table.columns
                 if not _is_pii(table.name, c.name))
    return Table(f"raw_{table.name.lower()}", cols + _LOAD_META, grain=table.grain)


def ingest_raw(src_dir: Path, sources: dict[str, Table], file_names: dict[str, str],
               batch_id: str, load_ts: datetime) -> dict[str, pd.DataFrame]:
    """Read and header-check all sources, then drop the PII columns.

    The header check sees the full contract, so a renamed PII column still
    fails. The drop happens in memory, before anything is written, so no PII
    name or value reaches the raw layer. Raises SchemaError before anything is written.
    """
    frames = ingest_all(src_dir, sources, file_names, batch_id, load_ts)
    dropped = pii_columns(sources)
    return {name: df.drop(columns=list(dropped.get(name, ()))).rename(columns=_RENAME)
            for name, df in frames.items()}


def land_raw(raw: dict[str, pd.DataFrame], sources: dict[str, Table], db_path: Path) -> None:
    with Warehouse(db_path) as wh:
        for name, df in raw.items():
            wh.replace(raw_table(sources[name]), df)


def row_counts(raw: dict[str, pd.DataFrame], file_names: dict[str, str]) -> dict[str, int]:
    return {file_names[name]: len(df) for name, df in raw.items()}


def write_manifest(out_dir: Path, batch_id: str, load_ts: datetime, counts: dict[str, int],
                   dropped: dict[str, int]) -> Path:
    """Counts only: rows per file and PII columns dropped per file. No column name or value."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "raw_manifest.json"
    path.write_text(json.dumps({"dp_batch_id": batch_id, "dp_load_ts": load_ts.isoformat(sep=" "),
                                "row_counts": counts,
                                "pii_columns_dropped": dropped},
                               indent=2), encoding="utf-8")
    return path


def pii_columns(sources: dict[str, Table]) -> dict[str, tuple[str, ...]]:
    """Per source, the columns FR-07's PII rule and the PRD's PII columns cover."""
    found = {name: tuple(c for c in t.column_names if _is_pii(name, c)) for name, t in sources.items()}
    return {name: cols for name, cols in found.items() if cols}


@dataclass
class RawResult:
    batch_id: str
    load_ts: datetime
    row_counts: dict[str, int]
    db_path: Path
    manifest_path: Path


def build(src_dir: Path = config.SOURCE_DIR, db_path: Path = config.DB_PATH, out_dir: Path = config.OUT_DIR,
          batch_id: str | None = None, load_ts: datetime | None = None) -> RawResult:
    batch_id = batch_id or str(uuid.uuid4())
    load_ts = load_ts or datetime.now().replace(microsecond=0)

    raw = ingest_raw(Path(src_dir), SOURCES, config.SOURCE_FILES, batch_id, load_ts)
    land_raw(raw, SOURCES, Path(db_path))
    counts = row_counts(raw, config.SOURCE_FILES)
    manifest = write_manifest(Path(out_dir), batch_id, load_ts, counts,
                              {config.SOURCE_FILES[name]: len(cols) for name, cols in pii_columns(SOURCES).items()})
    return RawResult(batch_id, load_ts, counts, Path(db_path), manifest)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="DP_Account_Daily_Balance FR-01: land the core banking extracts in raw")
    parser.add_argument("--src-dir", type=Path, default=config.SOURCE_DIR)
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    parser.add_argument("--out-dir", type=Path, default=config.OUT_DIR)
    args = parser.parse_args(argv)
    res = build(args.src_dir, args.db, args.out_dir)
    print(f"batch: {res.batch_id}   loaded: {res.load_ts}")
    for name, rows in res.row_counts.items():
        print(f"  {name}: {rows} rows")


if __name__ == "__main__":
    main()
