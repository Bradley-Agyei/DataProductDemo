"""Data quality rule engine and reusable rule factories.

Severity decides what a failure does:
  block  - the run must not publish
  reject - failing rows are removed and logged; the run continues
  warn   - recorded only
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import pandas as pd

from .contract import Table
from .standardize import REJECT_COLUMNS, row_key

BLOCK, REJECT, WARN = "block", "reject", "warn"
_FAIL_STATUS = {BLOCK: "Fail", REJECT: "Reject", WARN: "Warn"}

Frames = Mapping[str, pd.DataFrame]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    table: str
    severity: str
    # Returns a boolean mask of failing rows, or a failure count for table-level checks.
    check: Callable[[Frames], "pd.Series | int"]
    # Optional switch for rules that only apply when configured; when False the rule passes with 0 rows checked.
    applies: Callable[[Frames], bool] | None = None


@dataclass
class DqOutcome:
    results: pd.DataFrame
    frames: dict[str, pd.DataFrame]
    rejects: pd.DataFrame

    @property
    def blocked(self) -> bool:
        failed = self.results[(self.results["severity"] == BLOCK) & (self.results["rows_failed"] > 0)]
        return not failed.empty


def run_rules(rules: list[Rule], frames: Frames, contracts: Mapping[str, Table]) -> DqOutcome:
    """Rules run in order; later rules see rows already removed by earlier reject rules."""
    frames = dict(frames)
    results, rejects = [], []
    for rule in rules:
        df = frames[rule.table]
        if rule.applies is not None and not rule.applies(frames):
            results.append({"rule_id": rule.rule_id, "description": rule.description, "table_name": rule.table,
                            "severity": rule.severity, "rows_checked": 0, "rows_failed": 0, "status": "Pass"})
            continue
        outcome = rule.check(frames)
        if isinstance(outcome, pd.Series):
            mask = outcome.reindex(df.index, fill_value=False).astype(bool)
            failed = int(mask.sum())
        else:
            mask, failed = None, int(outcome)

        if rule.severity == REJECT and failed:
            if mask is None:
                raise ValueError(f"{rule.rule_id}: reject rules must return a row mask")
            contract = contracts[rule.table]
            rejects.extend({"table_name": rule.table, "row_key": row_key(r, contract), "column_name": None,
                            "raw_value": None, "reason": f"{rule.rule_id}: {rule.description}"}
                           for r in df[mask].to_dict("records"))
            frames[rule.table] = df[~mask]

        results.append({"rule_id": rule.rule_id, "description": rule.description, "table_name": rule.table,
                        "severity": rule.severity, "rows_checked": len(df), "rows_failed": failed,
                        "status": _FAIL_STATUS[rule.severity] if failed else "Pass"})
    return DqOutcome(pd.DataFrame(results), frames, pd.DataFrame(rejects, columns=REJECT_COLUMNS))


def unique_not_null(rule_id: str, table: str, column: str, severity: str = BLOCK) -> Rule:
    def check(frames: Frames) -> pd.Series:
        s = frames[table][column]
        return s.isna() | s.duplicated(keep=False)
    return Rule(rule_id, f"{column} is unique and not null", table, severity, check)


def matches_pattern(rule_id: str, contract: Table, severity: str = BLOCK) -> Rule:
    cols = [c for c in contract.columns if c.pattern]

    def check(frames: Frames) -> pd.Series:
        df = frames[contract.name]
        mask = pd.Series(False, index=df.index)
        for c in cols:
            s = df[c.name]
            mask |= s.notna() & ~s.astype(str).str.fullmatch(c.pattern).fillna(False).astype(bool)
        return mask
    names = ", ".join(c.name for c in cols)
    return Rule(rule_id, f"{names} match the contract pattern", contract.name, severity, check)


def required_present(rule_id: str, contract: Table, severity: str = BLOCK) -> Rule:
    """Pending columns are skipped until their feed is live."""
    cols = [c.name for c in contract.columns if not c.nullable and not c.is_pending]

    def check(frames: Frames) -> pd.Series:
        return frames[contract.name][cols].isna().any(axis=1)
    return Rule(rule_id, "all ready NOT NULL columns are populated", contract.name, severity, check)


def allowed_values(rule_id: str, contract: Table, severity: str = BLOCK) -> Rule:
    cols = [c for c in contract.columns if c.allowed]

    def check(frames: Frames) -> pd.Series:
        df = frames[contract.name]
        mask = pd.Series(False, index=df.index)
        for c in cols:
            s = df[c.name]
            mask |= s.notna() & ~s.isin(list(c.allowed))
        return mask
    return Rule(rule_id, "category columns contain only allowed values", contract.name, severity, check)


def foreign_keys_resolve(rule_id: str, contract: Table, severity: str = REJECT) -> Rule:
    fks = [(c.name, *c.foreign_key) for c in contract.columns if c.foreign_key]

    def check(frames: Frames) -> pd.Series:
        df = frames[contract.name]
        mask = pd.Series(False, index=df.index)
        for column, parent, parent_col in fks:
            valid = list(set(frames[parent][parent_col]))
            mask |= df[column].notna() & ~df[column].isin(valid)
        return mask
    parents = ", ".join(sorted({p for _, p, _ in fks}))
    return Rule(rule_id, f"{contract.name} foreign keys resolve ({parents})", contract.name, severity, check)
