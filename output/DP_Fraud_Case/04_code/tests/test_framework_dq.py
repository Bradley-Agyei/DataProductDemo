"""DQ rule engine behaviour shared by every data product."""
import pandas as pd

from src.dp_framework.contract import Column, Table
from src.dp_framework.dq import BLOCK, REJECT, WARN, Rule, run_rules

ITEMS = Table("items", (Column("item_id", "VARCHAR(5)", key="PK"), Column("qty", "INT")))


def frames():
    return {"items": pd.DataFrame({"item_id": ["a", "b", "c"], "qty": [1, -1, 5]}, dtype=object)}


def negative(f):
    return f["items"]["qty"] < 0


def test_reject_rule_removes_and_logs_rows():
    out = run_rules([Rule("R1", "qty >= 0", "items", REJECT, negative)], frames(), {"items": ITEMS})
    assert list(out.frames["items"]["item_id"]) == ["a", "c"]
    assert out.rejects[["row_key", "reason"]].values.tolist() == [["b", "R1: qty >= 0"]]
    assert not out.blocked


def test_block_rule_with_count_blocks():
    out = run_rules([Rule("R2", "3 rows", "items", BLOCK, lambda f: abs(len(f["items"]) - 4))], frames(), {})
    assert out.blocked and out.results.loc[0, "status"] == "Fail"


def test_rule_that_does_not_apply_passes_with_zero_rows_checked():
    rule = Rule("R3", "optional", "items", WARN, negative, applies=lambda f: False)
    out = run_rules([rule], frames(), {})
    assert out.results.loc[0, ["rows_checked", "rows_failed", "status"]].tolist() == [0, 0, "Pass"]


def test_rule_that_applies_runs_normally():
    rule = Rule("R4", "optional", "items", WARN, negative, applies=lambda f: True)
    out = run_rules([rule], frames(), {})
    assert out.results.loc[0, ["rows_checked", "rows_failed", "status"]].tolist() == [3, 1, "Warn"]
