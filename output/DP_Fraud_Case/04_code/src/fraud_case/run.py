"""Build DP_Fraud_Case end to end: ingest -> standardize -> lifecycle DQ -> derive -> product DQ -> publish.

    python -m src.fraud_case.run [--src DIR] [--member-ref FILE] [--account-ref FILE] [--db FILE] [--out DIR]
                                 [--as-of YYYY-MM-DD]
    python -m src.fraud_case.run --write-ddl
"""
from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from contracts.fraud_case import DQ_EXCEPTIONS, FRAUD_CASE, FRAUD_CASE_STATUS_SNAPSHOT
from contracts.sources import FRAUD_CASE_EXTRACT, SOURCES
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
from .transform import (build_fraud_case, build_status_snapshot, load_account_reference, load_member_reference,
                        member_match_rate)

SUCCESS, BLOCKED = "SUCCESS", "BLOCKED"
EXTRACT = FRAUD_CASE_EXTRACT.name
DDL_TABLES = [FRAUD_CASE, DQ_EXCEPTIONS, REJECTS, DQ_RESULTS, RUN_LOG, FRAUD_CASE_STATUS_SNAPSHOT]
CONTRACTS = {**SOURCES, FRAUD_CASE.name: FRAUD_CASE}


@dataclass
class RunResult:
    batch_id: str
    status: str
    product: pd.DataFrame
    staged: dict[str, pd.DataFrame]
    rejects: pd.DataFrame
    dq_results: pd.DataFrame
    exceptions: pd.DataFrame
    run_log: pd.DataFrame
    db_path: Path
    out_dir: Path


def build(src_dir: Path = config.SOURCE_DIR, member_ref: Path = config.MEMBER_REFERENCE_CSV,
          db_path: Path = config.DB_PATH, out_dir: Path = config.OUT_DIR, as_of: date | None = None,
          settings: Settings = Settings(), batch_id: str | None = None,
          load_ts: datetime | None = None, account_ref: Path = config.ACCOUNT_REFERENCE_CSV) -> RunResult:
    as_of = as_of or date.today()
    batch_id = batch_id or str(uuid.uuid4())
    load_ts = load_ts or datetime.now().replace(microsecond=0)
    member_ids = load_member_reference(member_ref)
    account_in_core = load_account_reference(account_ref, config.ACCOUNT_SOURCE_SYSTEM)

    raw = ingest_all(src_dir, SOURCES, config.SOURCE_FILES, batch_id, load_ts)
    staged, type_rejects = standardize(raw[EXTRACT], FRAUD_CASE_EXTRACT)

    source_dq = run_rules(source_rules(as_of, settings), {EXTRACT: staged}, CONTRACTS)
    staged = source_dq.frames[EXTRACT]

    product = build_fraud_case(staged, member_ids, account_in_core, settings.sla_days_by_priority, as_of, load_ts,
                               batch_id)
    rules = product_rules(len(staged), member_match_rate(product), settings)
    product_dq = run_rules(rules, {FRAUD_CASE.name: product}, CONTRACTS)
    product = product_dq.frames[FRAUD_CASE.name].reset_index(drop=True)

    status = BLOCKED if source_dq.blocked or product_dq.blocked else SUCCESS
    exceptions = find_exceptions(product, batch_id)
    dq_results = pd.concat([source_dq.results, product_dq.results], ignore_index=True).assign(
        dp_batch_id=batch_id, run_ts=load_ts)
    rejects = pd.concat([r for r in (type_rejects, source_dq.rejects, product_dq.rejects) if not r.empty]
                        or [pd.DataFrame(columns=REJECT_COLUMNS)], ignore_index=True).assign(dp_batch_id=batch_id)
    run_log = pd.DataFrame([
        {"table_name": staged_table(FRAUD_CASE_EXTRACT).name, "layer": "staging", "rows_in": len(raw[EXTRACT]),
         "rows_out": len(staged), "rows_rejected": len(raw[EXTRACT]) - len(staged), "status": "OK"},
        {"table_name": FRAUD_CASE.name, "layer": "product", "rows_in": len(staged), "rows_out": len(product),
         "rows_rejected": len(staged) - len(product), "status": status},
    ]).assign(dp_batch_id=batch_id, run_ts=load_ts)

    with Warehouse(db_path) as wh:
        wh.replace(raw_table(FRAUD_CASE_EXTRACT), raw[EXTRACT])
        wh.replace(staged_table(FRAUD_CASE_EXTRACT), staged)
        wh.append(REJECTS, rejects)
        wh.append(DQ_RESULTS, dq_results)
        wh.append(RUN_LOG, run_log)
        wh.replace(DQ_EXCEPTIONS, exceptions)
        if status == SUCCESS:
            wh.replace(FRAUD_CASE, product)
            wh.replace_partition(FRAUD_CASE_STATUS_SNAPSHOT, build_status_snapshot(product, as_of, batch_id),
                                 "snapshot_date", as_of)

    out_dir = Path(out_dir)
    if status == SUCCESS:
        write_contract(FRAUD_CASE, out_dir, {**config.CONTRACT_META, "dp_batch_id": batch_id})
        export_csv(product, FRAUD_CASE, out_dir / "fraud_case.csv")
        export_csv(exceptions, DQ_EXCEPTIONS, out_dir / "dq_exceptions.csv")

    return RunResult(batch_id, status, product, {EXTRACT: staged}, rejects, dq_results, exceptions, run_log,
                     Path(db_path), out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the DP_Fraud_Case data product.")
    parser.add_argument("--src", type=Path, default=config.SOURCE_DIR, help="folder with DP_Fraud_Case.csv")
    parser.add_argument("--member-ref", type=Path, default=config.MEMBER_REFERENCE_CSV,
                        help="member_360.csv published by DP_Member_360")
    parser.add_argument("--account-ref", type=Path, default=config.ACCOUNT_REFERENCE_CSV,
                        help="account ID mapping reference table")
    parser.add_argument("--db", type=Path, default=config.DB_PATH, help="SQLite database file")
    parser.add_argument("--out", type=Path, default=config.OUT_DIR, help="folder for CSV + data contract")
    parser.add_argument("--as-of", type=date.fromisoformat, default=None, help="run date (default: today)")
    parser.add_argument("--write-ddl", action="store_true", help="regenerate sql/ddl from the contracts and exit")
    args = parser.parse_args(argv)

    if args.write_ddl:
        for path in write_ddl(DDL_TABLES, config.DDL_DIR):
            print(f"wrote {path}")
        return 0

    res = build(args.src, args.member_ref, args.db, args.out, args.as_of, account_ref=args.account_ref)
    print(f"Status: {res.status}   batch: {res.batch_id}")
    print(f"fraud_case rows: {len(res.product)}   rejects: {len(res.rejects)}   exceptions: {len(res.exceptions)}")
    print(res.dq_results[["rule_id", "table_name", "severity", "rows_checked", "rows_failed", "status"]]
          .to_string(index=False))
    if res.status == SUCCESS:
        print(f"Published: {res.out_dir / 'fraud_case.csv'}  |  contract: {res.out_dir / 'data_contract.md'}")
    return 0 if res.status == SUCCESS else 1


if __name__ == "__main__":
    sys.exit(main())
