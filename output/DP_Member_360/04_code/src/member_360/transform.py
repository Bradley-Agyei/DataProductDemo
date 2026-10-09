"""Member 360 business rules: one small function per rule in the source-to-target mapping."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from contracts.member_360 import MEMBER_360
from src.dp_framework.types import to_date

from .config import AGE_BANDS, Settings

_SOURCE_ID = re.compile(r"M(\d+)")


def conform_member_id(source_id: str, width: int = 6) -> str:
    """M0001 -> M000001. Raises if the ID is malformed or too long to fit the standard."""
    match = _SOURCE_ID.fullmatch(str(source_id).strip())
    if not match:
        raise ValueError(f"unrecognised member ID: {source_id!r}")
    digits = match.group(1).lstrip("0") or "0"
    if len(digits) > width:
        raise ValueError(f"member ID {source_id!r} exceeds {width} digits")
    return f"M{int(digits):0{width}d}"


def load_mapped_account_ids(path, source_system: str) -> set[str]:
    """Source account IDs that the shared mapping reference table maps for one source system."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"account ID mapping reference table not found: {path}")
    ref = pd.read_csv(path, dtype=str, keep_default_na=False)
    return set(ref.loc[ref["source_system"] == source_system, "source_account_id"].str.strip())


def build_xref(member: pd.DataFrame, load_ts: datetime, settings: Settings) -> pd.DataFrame:
    return pd.DataFrame({
        "source_member_id": member["member_id"].tolist(),
        "member_id": [conform_member_id(m, settings.id_width) for m in member["member_id"]],
        "source_system": settings.source_system,
        "dp_load_ts": load_ts,
    }, dtype=object)


def relationship_status(member: pd.DataFrame, account: pd.DataFrame, restricted_rule: bool) -> pd.Series:
    """member_status, overridden to Restricted when the member holds any Restricted account."""
    status = member["member_status"].copy()
    if restricted_rule:
        restricted = set(account.loc[account["account_status"] == "Restricted", "member_id"])
        status[member["member_id"].isin(list(restricted))] = "Restricted"
    return status


def age_band(birth_date: date, as_of: date) -> str | None:
    """Ready for the DOB feed: only the band is ever published, never the date."""
    age = as_of.year - birth_date.year - ((as_of.month, as_of.day) < (birth_date.month, birth_date.day))
    for low, high, label in AGE_BANDS:
        if age >= low and (high is None or age <= high):
            return label
    return None


def digital_enrolled_proxy(member: pd.DataFrame, transaction: pd.DataFrame, as_of: date,
                           settings: Settings) -> pd.Series:
    """TRUE when the member used a digital channel within the lookback window."""
    start = as_of - timedelta(days=settings.digital_lookback_days)
    in_window = [start <= to_date(k) <= as_of for k in transaction["date_key"]]
    digital = transaction["channel_id"].isin(list(settings.digital_channels))
    active = set(transaction.loc[digital & pd.Series(in_window, index=transaction.index), "member_id"])
    return pd.Series([m in active for m in member["member_id"]], index=member.index, dtype=object)


def attach_pending_attributes(product: pd.DataFrame, member: pd.DataFrame, transaction: pd.DataFrame,
                              as_of: date, settings: Settings) -> pd.DataFrame:
    """Columns without a source feed are published as NULL so the shape is stable for consumers."""
    out = product.copy()
    for col in MEMBER_360.columns:
        if col.is_pending:
            out[col.name] = None
    if settings.digital_proxy:
        out["digital_enrolled_flag"] = digital_enrolled_proxy(member, transaction, as_of, settings)
    return out


def build_member_360(staged: dict[str, pd.DataFrame], as_of: date, load_ts: datetime, batch_id: str,
                     settings: Settings) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (product, member_id_xref)."""
    member, account, transaction = staged["Member"], staged["Account"], staged["Transaction"]
    xref = build_xref(member, load_ts, settings)
    id_map = dict(zip(xref["source_member_id"], xref["member_id"]))

    product = pd.DataFrame({
        "member_id": member["member_id"].map(id_map),
        "member_since_date": member["join_date"],
        "member_segment": member["member_segment"],
        "home_state": member["state"],
        "relationship_status": relationship_status(member, account, settings.restricted_rule),
    }, dtype=object)
    product = attach_pending_attributes(product, member, transaction, as_of, settings)
    product["dp_load_ts"] = load_ts
    product["dp_batch_id"] = batch_id
    return product[MEMBER_360.column_names].reset_index(drop=True), xref
