"""PII guard: mask every PII value with * before anything is written.

The product contract has no PII column, so this is defence in depth: a PII
column that reaches the publish step (from an upstream frame, or a reject's
raw value) is masked, never written as received.
"""
from __future__ import annotations

import re

import pandas as pd

from . import config

_RULE_ID = re.compile(r"^(DQ-\d+)")


def pii_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if config.is_pii_column(c)]


def mask_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Every value in a PII-named column becomes PII_MASK; the column itself stays."""
    cols = pii_columns(df)
    return df.assign(**{c: config.PII_MASK for c in cols}) if cols else df


def _safe_reason(reason, column: str) -> str:
    """Framework parse errors quote the raw value, so a PII reject's reason is rewritten whole."""
    match = _RULE_ID.match(str(reason or ""))
    prefix = f"{match.group(1)}: " if match else ""
    return f"{prefix}{column} failed its check; value masked ({config.PII_MASK})"


def mask_reject_values(rejects: pd.DataFrame) -> pd.DataFrame:
    """A reject on a PII column keeps its rule ID, but its raw value and reason text are masked."""
    if rejects.empty or "column_name" not in rejects or "raw_value" not in rejects:
        return rejects
    hit = rejects["column_name"].map(lambda c: c is not None and config.is_pii_column(c))
    out = rejects.copy()
    out.loc[hit, "raw_value"] = config.PII_MASK
    out.loc[hit, "reason"] = [_safe_reason(r, c) for r, c in zip(out.loc[hit, "reason"], out.loc[hit, "column_name"])]
    return out
