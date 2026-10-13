"""FR-07 (SCRUM-43): publish account_daily_balance behind the DQ gate.

FR-01 to FR-06 (ingest, standardize, totals, roll-forward, overdraft, attributes)
build the product frame and the counted transactions; `publish` takes them from
there:

    mask PII -> product DQ -> exception report -> run log -> write

Warnings raised upstream (DQ-13 and DQ-14 from FR-06) come in as
`upstream_warnings`: they are added to the exception report and DQ results and
never block.

Critical rules (DQ-01..07, DQ-10) block: the product table, CSV and data
contract are only replaced on SUCCESS, so a blocked run leaves the previous
product in place. Rejects, DQ results, exceptions and the run log are always
written. A rerun with the same inputs replaces the product with the same rows.

    python -m src.account_daily_balance.run --write-ddl
"""
from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE, DQ_EXCEPTIONS
from src.dp_framework.dq import WARN, run_rules
from src.dp_framework.load import Warehouse
from src.dp_framework.ops_tables import DQ_RESULTS, REJECTS, RUN_LOG
from src.dp_framework.publish import export_csv, write_contract, write_ddl
from src.dp_framework.standardize import REJECT_COLUMNS

from . import config
from .dq_rules import PRODUCT, UPSTREAM_WARNINGS, product_rules
from .exceptions import find_exceptions
from .pii import mask_pii, mask_reject_values

SUCCESS, BLOCKED = "SUCCESS", "BLOCKED"
DDL_TABLES = [ACCOUNT_DAILY_BALANCE, DQ_EXCEPTIONS, REJECTS, DQ_RESULTS, RUN_LOG]
CONTRACTS = {PRODUCT: ACCOUNT_DAILY_BALANCE}


@dataclass
class PublishResult:
    batch_id: str
    status: str
    product: pd.DataFrame
    rejects: pd.DataFrame
    dq_results: pd.DataFrame
    exceptions: pd.DataFrame
    run_log: pd.DataFrame
    db_path: Path
    out_dir: Path


def publish(product: pd.DataFrame, counted_transactions: pd.DataFrame,
            upstream_rejects: pd.DataFrame | None = None, upstream_warnings: list[dict] | None = None,
            batch_id: str | None = None,
            load_ts: datetime | None = None, db_path: Path = config.DB_PATH,
            out_dir: Path = config.OUT_DIR) -> PublishResult:
    batch_id = batch_id or str(uuid.uuid4())
    load_ts = load_ts or datetime.now().replace(microsecond=0)

    product = mask_pii(product).assign(dp_load_ts=load_ts, dp_batch_id=batch_id)
    upstream = upstream_rejects if upstream_rejects is not None else pd.DataFrame(columns=REJECT_COLUMNS)

    rules = product_rules(counted_transactions)
    outcome = run_rules(rules, {PRODUCT: product}, CONTRACTS)
    status = BLOCKED if outcome.blocked else SUCCESS
    product = outcome.frames[PRODUCT].reset_index(drop=True)

    rejects = mask_reject_values(pd.concat([r for r in (upstream, outcome.rejects) if not r.empty]
                                           or [pd.DataFrame(columns=REJECT_COLUMNS)], ignore_index=True))
    rejects = rejects.assign(dp_batch_id=batch_id)
    warnings = list(upstream_warnings or [])
    exceptions = find_exceptions(rejects, rules, {PRODUCT: product}, batch_id, warnings)
    dq_results = pd.concat([outcome.results, _upstream_results(warnings)], ignore_index=True
                           ).assign(dp_batch_id=batch_id, run_ts=load_ts)
    rows_in = len(outcome.frames[PRODUCT]) + len(outcome.rejects)
    run_log = pd.DataFrame([{"table_name": PRODUCT, "layer": "product", "rows_in": rows_in,
                             "rows_out": len(product) if status == SUCCESS else 0,
                             "rows_rejected": len(outcome.rejects), "status": status}]
                           ).assign(dp_batch_id=batch_id, run_ts=load_ts)

    with Warehouse(db_path) as wh:
        wh.append(REJECTS, rejects)
        wh.append(DQ_RESULTS, dq_results)
        wh.append(RUN_LOG, run_log)
        wh.replace(DQ_EXCEPTIONS, exceptions)
        if status == SUCCESS:
            wh.replace(ACCOUNT_DAILY_BALANCE, product)

    out_dir = Path(out_dir)
    export_csv(exceptions, DQ_EXCEPTIONS, out_dir / "dq_exceptions.csv")
    export_csv(run_log, RUN_LOG, out_dir / "run_log.csv")
    if status == SUCCESS:
        write_contract(ACCOUNT_DAILY_BALANCE, out_dir, {**config.CONTRACT_META, "dp_batch_id": batch_id})
        export_csv(product, ACCOUNT_DAILY_BALANCE, out_dir / "account_daily_balance.csv")

    return PublishResult(batch_id, status, product, rejects, dq_results, exceptions, run_log, Path(db_path), out_dir)


def _upstream_results(warnings: list[dict]) -> pd.DataFrame:
    """One DQ result per upstream warning rule; warnings never block."""
    counts = pd.Series([w["rule_id"] for w in warnings], dtype=object).value_counts().sort_index()
    return pd.DataFrame([{"rule_id": rule_id, "description": UPSTREAM_WARNINGS.get(rule_id, ""),
                          "table_name": PRODUCT, "severity": WARN, "rows_checked": int(n), "rows_failed": int(n),
                          "status": "Warn"} for rule_id, n in counts.items()],
                        columns=["rule_id", "description", "table_name", "severity", "rows_checked",
                                 "rows_failed", "status"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DP_Account_Daily_Balance publish (FR-07).")
    parser.add_argument("--write-ddl", action="store_true", help="regenerate sql/ddl from the contracts and exit")
    args = parser.parse_args(argv)
    if args.write_ddl:
        for path in write_ddl(DDL_TABLES, config.DDL_DIR):
            print(f"wrote {path}")
        return 0
    parser.error("the end-to-end build needs FR-01 to FR-06 (SCRUM-37 to SCRUM-42); only --write-ddl is available")
    return 2


if __name__ == "__main__":
    sys.exit(main())
