"""FR-02 (SCRUM-38): type and conform the core banking raw extracts."""
from __future__ import annotations

import re
from typing import Mapping

import pandas as pd

from contracts.sources import SOURCES
from src.account_daily_balance import config
from src.dp_framework.contract import Table
from src.dp_framework.standardize import REJECT_COLUMNS, row_key, standardize

ACCOUNT_ID_PATTERN = re.compile(r"A\d{7}")
MEMBER_ID_PATTERN = re.compile(r"M(\d{1,6})")
ACCOUNT_MAP_COLUMNS = {"source_system", "source_account_id", "account_id", "in_core_banking"}


def _account_id_map(mapping: pd.DataFrame | None) -> dict[str, str]:
    if mapping is None:
        mapping = pd.read_csv(config.ACCOUNT_ID_MAP_PATH, dtype=str, keep_default_na=False,
                              encoding="utf-8-sig")
    missing = ACCOUNT_MAP_COLUMNS - set(mapping.columns)
    if missing:
        raise ValueError(f"account_id_map is missing required columns: {sorted(missing)}")

    core = mapping.loc[
        mapping["source_system"].astype(str).str.strip().eq("core_banking")
        & mapping["in_core_banking"].astype(str).str.strip().str.upper().eq("TRUE"),
        ["source_account_id", "account_id"],
    ].copy()
    if core["source_account_id"].duplicated().any():
        raise ValueError("account_id_map contains duplicate core banking source IDs")
    if not core["account_id"].astype(str).map(lambda value: bool(ACCOUNT_ID_PATTERN.fullmatch(value))).all():
        raise ValueError("account_id_map contains an invalid canonical account ID")
    return dict(zip(core["source_account_id"].astype(str), core["account_id"].astype(str)))


def _conform_member_id(value):
    match = MEMBER_ID_PATTERN.fullmatch(str(value).strip())
    return f"M{match.group(1).zfill(6)}" if match else value


def _map_account_ids(table_name: str, frame: pd.DataFrame, mapping: dict[str, str]
                     ) -> tuple[pd.DataFrame, list[dict]]:
    if "account_id" not in frame.columns:
        return frame, []
    converted, rejects = [], []
    for record in frame.to_dict("records"):
        raw_id = record["account_id"]
        canonical = mapping.get(str(raw_id).strip())
        if canonical is None:
            keys = SOURCES[table_name].primary_key
            row_key = "|".join(str(record.get(key, "")) for key in keys) or str(raw_id)
            rejects.append({
                "table_name": table_name,
                "row_key": row_key,
                "column_name": "account_id",
                "raw_value": raw_id,
                "reason": "DQ-08",
            })
            continue
        record["account_id"] = canonical
        converted.append(record)
    return pd.DataFrame(converted, columns=frame.columns, dtype=object), rejects


def _reject_duplicate_unique_keys(frame: pd.DataFrame, table: Table) -> tuple[pd.DataFrame, list[dict]]:
    duplicate_rows = pd.Series(False, index=frame.index)
    rejects = []
    for column in table.columns:
        if column.key != "UNIQUE" or frame.empty:
            continue
        duplicate = frame.duplicated(subset=[column.name], keep=False)
        duplicate_rows |= duplicate
        rejects.extend({
            "table_name": table.name,
            "row_key": row_key(record, table),
            "column_name": column.name,
            "raw_value": None,
            "reason": "duplicate unique key",
        } for record in frame[duplicate].to_dict("records"))
    return frame[~duplicate_rows].reset_index(drop=True), rejects


def standardize_sources(raw_tables: Mapping[str, pd.DataFrame],
                        account_id_map: pd.DataFrame | None = None
                        ) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Return typed source frames and row-level rejects from FR-01 raw frames.

    Member source frames contain only the non-PII columns retained by FR-01.
    """
    missing = set(SOURCES) - set(raw_tables)
    if missing:
        raise ValueError(f"missing raw source tables: {sorted(missing)}")
    account_map = _account_id_map(account_id_map)
    typed, rejects = {}, []

    for name, table in SOURCES.items():
        frame = raw_tables[name].copy()
        frame, unmapped = _map_account_ids(name, frame, account_map)
        rejects.extend(unmapped)
        if "member_id" in frame.columns:
            frame["member_id"] = frame["member_id"].map(_conform_member_id)
        standardized, rejected = standardize(frame, table)
        standardized, unique_rejects = _reject_duplicate_unique_keys(standardized, table)
        typed[name] = standardized
        if not rejected.empty:
            rejects.extend(rejected.to_dict("records"))
        rejects.extend(unique_rejects)

    return typed, pd.DataFrame(rejects, columns=REJECT_COLUMNS)
