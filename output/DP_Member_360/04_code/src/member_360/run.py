"""Build DP_Member_360 end to end: ingest -> standardize -> DQ -> transform -> DQ -> publish.

    python -m src.member_360.run [--src DIR] [--db FILE] [--out DIR] [--as-of YYYY-MM-DD]
    python -m src.member_360.run --write-ddl
"""
from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from contracts.member_360 import DQ_EXCEPTIONS, MEMBER_360, MEMBER_ID_XREF
from contracts.sources import SOURCES
from src.dp_framework.dq import run_rules
from src.dp_framework.ingest import ingest_all, raw_table, staged_table
from src.dp_framework.load import Warehouse
from src.dp_framework.ops_tables import DQ_RESULTS, REJECTS, RUN_LOG
from src.dp_framework.publish import export_csv, write_contract, write_ddl
from src.dp_framework.standardize import REJECT_COLUMNS, standardize

from . import config
from .config import Settings
from .dq_rules import product_rules, source_rules
from .exceptions import find_exceptions
from .transform import build_member_360, load_mapped_account_ids

SUCCESS, BLOCKED = "SUCCESS", "BLOCKED"
DDL_TABLES = [MEMBER_360, MEMBER_ID_XREF, DQ_EXCEPTIONS, REJECTS, DQ_RESULTS, RUN_LOG]
CONTRACTS = {**SOURCES, MEMBER_360.name: MEMBER_360}


@dataclass
class RunResult:
    batch_id: str
    status: str
    product: pd.DataFrame
    xref: pd.DataFrame
    staged: dict[str, pd.DataFrame]
    rejects: pd.DataFrame
    dq_results: pd.DataFrame
    exceptions: pd.DataFrame
    run_log: pd.DataFrame
    db_path: Path
    out_dir: Path


def build(src_dir: Path = config.SOURCE_DIR, db_path: Path = config.DB_PATH, out_dir: Path = config.OUT_DIR,
          as_of: date | None = None, settings: Settings = Settings(), batch_id: str | None = None,
          load_ts: datetime | None = None, account_ref: Path = config.ACCOUNT_REFERENCE_CSV) -> RunResult:
    as_of = as_of or date.today()
    batch_id = batch_id or str(uuid.uuid4())
    load_ts = load_ts or datetime.now().replace(microsecond=0)
    mapped_accounts = load_mapped_account_ids(account_ref, config.CORE_BANKING_SYSTEM)

    raw = ingest_all(src_dir, SOURCES, config.SOURCE_FILES, batch_id, load_ts)

    staged, rejects = {}, []
    for name, contract in SOURCES.items():
        staged[name], table_rejects = standardize(raw[name], contract)
        rejects.append(table_rejects)

    source_dq = run_rules(source_rules(mapped_accounts), staged, CONTRACTS)
    staged = source_dq.frames

    product, xref = build_member_360(staged, as_of, load_ts, batch_id, settings)
    product_dq = run_rules(product_rules(as_of, load_ts, staged["Member"]["member_id"].nunique()),
                           {MEMBER_360.name: product}, CONTRACTS)
    product = product_dq.frames[MEMBER_360.name].reset_index(drop=True)

    status = BLOCKED if source_dq.blocked or product_dq.blocked else SUCCESS
    id_map = dict(zip(xref["source_member_id"], xref["member_id"]))
    exceptions = find_exceptions(staged, id_map, batch_id)
    dq_results = pd.concat([source_dq.results, product_dq.results], ignore_index=True).assign(
        dp_batch_id=batch_id, run_ts=load_ts)
    all_rejects = pd.concat([r for r in rejects + [source_dq.rejects, product_dq.rejects] if not r.empty]
                            or [pd.DataFrame(columns=REJECT_COLUMNS)], ignore_index=True).assign(dp_batch_id=batch_id)
    run_log = _run_log(raw, staged, product, status, batch_id, load_ts)

    with Warehouse(db_path) as wh:
        for name, contract in SOURCES.items():
            wh.replace(raw_table(contract), raw[name])
            wh.replace(staged_table(contract), staged[name])
        wh.append(REJECTS, all_rejects)
        wh.append(DQ_RESULTS, dq_results)
        wh.append(RUN_LOG, run_log)
        wh.replace(DQ_EXCEPTIONS, exceptions)
        if status == SUCCESS:
            wh.replace(MEMBER_360, product)
            wh.replace(MEMBER_ID_XREF, xref)

    out_dir = Path(out_dir)
    if status == SUCCESS:
        write_contract(MEMBER_360, out_dir, {**config.CONTRACT_META, "dp_batch_id": batch_id})
        export_csv(product, MEMBER_360, out_dir / "member_360.csv")
        export_csv(exceptions, DQ_EXCEPTIONS, out_dir / "dq_exceptions.csv")

    return RunResult(batch_id, status, product, xref, staged, all_rejects, dq_results, exceptions, run_log,
                     Path(db_path), out_dir)


def _run_log(raw, staged, product, status, batch_id, load_ts) -> pd.DataFrame:
    rows = [{"table_name": f"stg_{name.lower()}", "layer": "staging", "rows_in": len(raw[name]),
             "rows_out": len(staged[name]), "rows_rejected": len(raw[name]) - len(staged[name]), "status": "OK"}
            for name in SOURCES]
    members = len(staged["Member"])
    rows.append({"table_name": MEMBER_360.name, "layer": "product", "rows_in": members,
                 "rows_out": len(product), "rows_rejected": members - len(product), "status": status})
    return pd.DataFrame(rows).assign(dp_batch_id=batch_id, run_ts=load_ts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the DP_Member_360 data product.")
    parser.add_argument("--src", type=Path, default=config.SOURCE_DIR, help="folder with the 8 source CSVs")
    parser.add_argument("--account-ref", type=Path, default=config.ACCOUNT_REFERENCE_CSV,
                        help="account ID mapping reference table")
    parser.add_argument("--db", type=Path, default=config.DB_PATH, help="SQLite database file")
    parser.add_argument("--out", type=Path, default=config.OUT_DIR, help="folder for CSV + data contract")
    parser.add_argument("--as-of", type=date.fromisoformat, default=None, help="run date (default: today)")
    parser.add_argument("--digital-proxy", action="store_true", help="derive digital_enrolled_flag from channels")
    parser.add_argument("--write-ddl", action="store_true", help="regenerate sql/ddl from the contracts and exit")
    args = parser.parse_args(argv)

    if args.write_ddl:
        for path in write_ddl(DDL_TABLES, config.DDL_DIR):
            print(f"wrote {path}")
        return 0

    res = build(args.src, args.db, args.out, args.as_of, Settings(digital_proxy=args.digital_proxy),
                account_ref=args.account_ref)
    print(f"Status: {res.status}   batch: {res.batch_id}")
    print(f"member_360 rows: {len(res.product)}   rejects: {len(res.rejects)}   exceptions: {len(res.exceptions)}")
    print(res.dq_results[["rule_id", "table_name", "severity", "rows_checked", "rows_failed", "status"]]
          .to_string(index=False))
    if res.status == SUCCESS:
        print(f"Published: {res.out_dir / 'member_360.csv'}  |  contract: {res.out_dir / 'data_contract.md'}")
    return 0 if res.status == SUCCESS else 1


if __name__ == "__main__":
    sys.exit(main())
