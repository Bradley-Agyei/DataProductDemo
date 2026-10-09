"""Typed staging: cast every column to its contract type; failing rows become rejects."""
from __future__ import annotations

import pandas as pd

from .contract import SchemaError, Table
from .types import ParseError, check_constraints, parse_value

REJECT_COLUMNS = ["table_name", "row_key", "column_name", "raw_value", "reason"]


def row_key(record: dict, table: Table) -> str:
    keys = table.primary_key or table.column_names[:1]
    return "|".join(str(record[k]) for k in keys)


def standardize(raw: pd.DataFrame, table: Table) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (typed rows, rejects). Extra frame columns (load metadata) pass through untouched."""
    missing = set(table.column_names) - set(raw.columns)
    if missing:
        raise SchemaError(f"{table.name}: missing columns {sorted(missing)}")
    passthrough = [c for c in raw.columns if c not in table.column_names]

    typed_rows, rejects = [], []
    for record in raw.to_dict("records"):
        row, errors = {}, []
        for col in table.columns:
            value = record[col.name]
            try:
                parsed = parse_value(value, col)
                check_constraints(parsed, col)
            except ParseError as exc:
                errors.append({"column_name": col.name, "raw_value": value, "reason": str(exc)})
                continue
            row[col.name] = parsed
        key = row_key(record, table)
        if errors:
            rejects.extend({"table_name": table.name, "row_key": key, **e} for e in errors)
        else:
            typed_rows.append({**row, **{c: record[c] for c in passthrough}})

    typed = pd.DataFrame(typed_rows, columns=table.column_names + passthrough, dtype=object)
    typed, dupes = _split_duplicate_keys(typed, table)
    return typed, pd.DataFrame(rejects + dupes, columns=REJECT_COLUMNS)


def _split_duplicate_keys(typed: pd.DataFrame, table: Table) -> tuple[pd.DataFrame, list[dict]]:
    """All copies of a duplicated key are rejected: there is no safe way to pick a winner."""
    if not table.primary_key or typed.empty:
        return typed, []
    dup = typed.duplicated(subset=table.primary_key, keep=False)
    rejects = [{"table_name": table.name, "row_key": row_key(r, table),
                "column_name": ",".join(table.primary_key), "raw_value": None,
                "reason": "duplicate primary key"}
               for r in typed[dup].to_dict("records")]
    return typed[~dup].reset_index(drop=True), rejects
