"""Build DP_Payment_Transaction. So far: FR-01 raw ingestion (SCRUM-44).

    python -m src.payment_transaction.run
"""
from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from contracts.sources import SOURCES
from src.payment_transaction import config
from src.payment_transaction.raw import ingest_raw, land_raw, row_counts, write_manifest


@dataclass
class RunResult:
    batch_id: str
    load_ts: datetime
    row_counts: dict[str, int]
    db_path: Path
    manifest_path: Path


def build(src_dir: Path = config.SOURCE_DIR, db_path: Path = config.DB_PATH, out_dir: Path = config.OUT_DIR,
          batch_id: str | None = None, load_ts: datetime | None = None) -> RunResult:
    batch_id = batch_id or str(uuid.uuid4())
    load_ts = load_ts or datetime.now().replace(microsecond=0)

    masked = config.PII_MASKED_COLUMNS
    raw = ingest_raw(Path(src_dir), SOURCES, config.SOURCE_FILES, batch_id, load_ts, masked, config.PII_MASK)
    land_raw(raw, SOURCES, Path(db_path))
    counts = row_counts(raw, config.SOURCE_FILES)
    manifest = write_manifest(Path(out_dir), batch_id, load_ts, counts,
                              {config.SOURCE_FILES[name]: cols for name, cols in masked.items()})
    return RunResult(batch_id, load_ts, counts, Path(db_path), manifest)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build DP_Payment_Transaction")
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
