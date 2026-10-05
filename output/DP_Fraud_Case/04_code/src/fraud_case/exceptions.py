"""Exception report for fraud operations: valid cases that still need a human look."""
from __future__ import annotations

import pandas as pd

from contracts.fraud_case import DQ_EXCEPTIONS

COLUMNS = [c for c in DQ_EXCEPTIONS.column_names if c != "dp_batch_id"]


def _row(exception_type: str, r: dict, detail: str) -> dict:
    return {"exception_type": exception_type, "case_id": r["case_id"], "member_id": r["member_id"], "detail": detail}


def members_not_found(product: pd.DataFrame) -> list[dict]:
    return [_row("MEMBER_NOT_FOUND", r, "member_id not in member_360; case kept")
            for r in product.to_dict("records") if r["member_found_flag"] is not True]


def accounts_not_found(product: pd.DataFrame) -> list[dict]:
    return [_row("ACCOUNT_NOT_FOUND", r, f"{r['primary_account_id']} not a core banking account; case kept")
            for r in product.to_dict("records") if r["account_found_flag"] is not True]


def open_cases_past_sla(product: pd.DataFrame) -> list[dict]:
    """Closed breaches are visible in sla_breached_flag but need no action, so only open cases are reported."""
    return [_row("CASE_SLA_BREACHED", r,
                 f"{r['priority']} {r['case_status']} for {r['case_age_days']} days (SLA {r['sla_days']})")
            for r in product.to_dict("records") if r["sla_breached_flag"] is True and not r["is_closed"]]


def find_exceptions(product: pd.DataFrame, batch_id: str) -> pd.DataFrame:
    rows = members_not_found(product) + accounts_not_found(product) + open_cases_past_sla(product)
    return pd.DataFrame(rows, columns=COLUMNS, dtype=object).assign(dp_batch_id=batch_id)
