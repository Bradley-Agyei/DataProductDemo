"""Fraud Case business rules: one small function per derived column."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Mapping

import pandas as pd

from contracts.fraud_case import FRAUD_CASE, FRAUD_CASE_STATUS_SNAPSHOT

CLOSED = "Closed"
_SECONDS_PER_DAY = Decimal(86_400)


def days_to_close(opened: datetime, closed: datetime | None) -> Decimal | None:
    if closed is None:
        return None
    seconds = Decimal(int((closed - opened).total_seconds()))
    return (seconds / _SECONDS_PER_DAY).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def case_age_days(opened: datetime, is_closed: bool, as_of: date) -> int | None:
    """Whole days from opening to the start of the run date; closed cases have no age."""
    if is_closed:
        return None
    return (datetime.combine(as_of, time()) - opened).days


def loss_confirmation_ratio(confirmed: Decimal, suspected: Decimal, is_closed: bool) -> Decimal | None:
    if not is_closed or not suspected:
        return None
    return (confirmed / suspected).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def sla_breached(days_closed: Decimal | None, age_days: int | None, sla_days: int) -> bool:
    """Closed cases are measured by time to close, open cases by age at the run date."""
    elapsed = days_closed if days_closed is not None else age_days
    return elapsed is not None and elapsed > sla_days


def load_member_reference(path: Path) -> set[str]:
    """Member IDs published by DP_Member_360."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"member_360 reference not found: {path}. "
                                "Build DP_Member_360 first or pass --member-ref.")
    return set(pd.read_csv(path, usecols=["member_id"], dtype=str)["member_id"].str.strip())


def load_account_reference(path: Path, source_system: str) -> dict[str, bool]:
    """Source account ID -> whether it maps to a core banking account, for one source system."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"account ID mapping reference table not found: {path}. "
                                "Run python -m tools.build_account_id_map or pass --account-ref.")
    ref = pd.read_csv(path, dtype=str, keep_default_na=False)
    ref = ref[ref["source_system"] == source_system]
    return dict(zip(ref["source_account_id"].str.strip(), ref["in_core_banking"].str.upper() == "TRUE"))


def build_fraud_case(extract: pd.DataFrame, member_ids: set[str], account_in_core: dict[str, bool],
                     sla_days_by_priority: Mapping[str, int], as_of: date, load_ts: datetime,
                     batch_id: str) -> pd.DataFrame:
    rows = []
    for r in extract.to_dict("records"):
        closed = r["case_status"] == CLOSED
        to_close = days_to_close(r["case_open_ts"], r["case_close_ts"]) if closed else None
        age = case_age_days(r["case_open_ts"], closed, as_of)
        sla = sla_days_by_priority[r["priority"]]
        rows.append({
            **{c: r[c] for c in extract.columns if c in FRAUD_CASE.column_names},
            "is_closed": closed,
            "days_to_close": to_close,
            "case_age_days": age,
            "loss_confirmation_ratio": loss_confirmation_ratio(
                r["confirmed_loss_amount"], r["suspected_loss_amount"], closed),
            "member_found_flag": r["member_id"] in member_ids,
            "account_found_flag": account_in_core.get(r["primary_account_id"], False),
            "sla_days": sla,
            "sla_breached_flag": sla_breached(to_close, age, sla),
            "dp_load_ts": load_ts,
            "dp_batch_id": batch_id,
        })
    return pd.DataFrame(rows, columns=FRAUD_CASE.column_names, dtype=object)


def build_status_snapshot(product: pd.DataFrame, as_of: date, batch_id: str) -> pd.DataFrame:
    snapshot = product[["case_id", "case_status", "priority", "assigned_queue"]].copy()
    snapshot.insert(0, "snapshot_date", as_of)
    snapshot["dp_batch_id"] = batch_id
    return snapshot[FRAUD_CASE_STATUS_SNAPSHOT.column_names].astype(object)


def member_match_rate(product: pd.DataFrame) -> float:
    if product.empty:
        return 1.0
    return sum(1 for f in product["member_found_flag"] if f is True) / len(product)
