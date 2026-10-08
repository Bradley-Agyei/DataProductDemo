"""Exception report: every rejected row and every warning, each with its DQ rule ID."""
from __future__ import annotations

import re

import pandas as pd

from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE, DQ_EXCEPTIONS
from src.dp_framework.dq import WARN, Rule
from src.dp_framework.standardize import row_key

COLUMNS = [c for c in DQ_EXCEPTIONS.column_names if c != "dp_batch_id"]
_RULE_ID = re.compile(r"^(DQ-\d+)")


def from_rejects(rejects: pd.DataFrame) -> list[dict]:
    rows = []
    for r in rejects.to_dict("records"):
        match = _RULE_ID.match(str(r["reason"]))
        rows.append({"exception_type": "REJECT", "rule_id": match.group(1) if match else "TYPE",
                     "table_name": r["table_name"], "row_key": r["row_key"], "detail": r["reason"]})
    return rows


def from_warnings(rules: list[Rule], frames) -> list[dict]:
    """Row-level warnings; a rule that returns a count is reported once for the table."""
    rows = []
    for rule in rules:
        if rule.severity != WARN or (rule.applies is not None and not rule.applies(frames)):
            continue
        outcome = rule.check(frames)
        df = frames[rule.table]
        if isinstance(outcome, pd.Series):
            for r in df[outcome.reindex(df.index, fill_value=False).astype(bool)].to_dict("records"):
                rows.append({"exception_type": "WARN", "rule_id": rule.rule_id, "table_name": rule.table,
                             "row_key": row_key(r, ACCOUNT_DAILY_BALANCE), "detail": rule.description})
        elif int(outcome):
            rows.append({"exception_type": "WARN", "rule_id": rule.rule_id, "table_name": rule.table,
                         "row_key": "", "detail": f"{rule.description} ({int(outcome)} rows)"})
    return rows


def find_exceptions(rejects: pd.DataFrame, rules: list[Rule], frames, batch_id: str) -> pd.DataFrame:
    rows = from_rejects(rejects) + from_warnings(rules, frames)
    return pd.DataFrame(rows, columns=COLUMNS, dtype=object).assign(dp_batch_id=batch_id)
