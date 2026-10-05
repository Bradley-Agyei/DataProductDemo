"""Case lifecycle and loss consistency rules (DQ-06..DQ-11)."""
from datetime import date

import pytest

from src.fraud_case.config import Settings
from tests.conftest import edit_extract, run_build

LIFECYCLE_RULES = ["DQ-06", "DQ-07", "DQ-08", "DQ-09", "DQ-10", "DQ-11"]


def status_of(res, rule_id):
    return res.dq_results.set_index("rule_id").loc[rule_id, "status"]


def rejected_cases(res, rule_id):
    return set(res.rejects.loc[res.rejects["reason"].str.startswith(rule_id), "row_key"])


@pytest.mark.parametrize("rule_id", LIFECYCLE_RULES)
def test_sample_passes_lifecycle_rules(result, rule_id):
    assert status_of(result, rule_id) == "Pass"


@pytest.mark.parametrize("old, new, case_id", [
    ("Digital Fraud,Confirmed Fraud,8/4/2026 16:00", "Digital Fraud,Confirmed Fraud,", "FC0000002"),
    ("Medium,$237.19 ,$0.00 ,Deposit Ops,,", "Medium,$237.19 ,$0.00 ,Deposit Ops,False Positive,", "FC0000001"),
    ("Enhanced Review,False Positive,8/6/2026 0:00", "Enhanced Review,,8/6/2026 0:00", "FC0000003"),
])
def test_incomplete_lifecycle_is_rejected(tmp_path, src_copy, old, new, case_id):
    edit_extract(src_copy, old, new)
    res = run_build(tmp_path, src_dir=src_copy)
    assert rejected_cases(res, "DQ-06") == {case_id}
    assert case_id not in set(res.product["case_id"])
    assert res.status == "SUCCESS"


def test_close_before_open_is_rejected(tmp_path, src_copy):
    edit_extract(src_copy, "Enhanced Review,False Positive,8/6/2026 0:00", "Enhanced Review,False Positive,7/30/2026 0:00")
    res = run_build(tmp_path, src_dir=src_copy)
    assert rejected_cases(res, "DQ-07") == {"FC0000003"}


def test_confirmed_above_suspected_is_rejected(tmp_path, src_copy):
    edit_extract(src_copy, "$374.38 ,$299.50", "$374.38 ,$399.50")
    res = run_build(tmp_path, src_dir=src_copy)
    assert rejected_cases(res, "DQ-08") == {"FC0000002"}


def test_false_positive_with_loss_warns_and_keeps_case(tmp_path, src_copy):
    edit_extract(src_copy, "$511.57 ,$0.00 ,Enhanced Review,False Positive", "$511.57 ,$10.00 ,Enhanced Review,False Positive")
    res = run_build(tmp_path, src_dir=src_copy)
    assert status_of(res, "DQ-09") == "Warn"
    assert "FC0000003" in set(res.product["case_id"])


def test_confirmed_fraud_without_loss_warns_by_default(tmp_path, src_copy):
    edit_extract(src_copy, "$374.38 ,$299.50", "$374.38 ,$0.00")
    res = run_build(tmp_path, src_dir=src_copy)
    assert status_of(res, "DQ-10") == "Warn"
    assert "FC0000002" in set(res.product["case_id"])


def test_confirmed_fraud_without_loss_can_be_rejected(tmp_path, src_copy):
    edit_extract(src_copy, "$374.38 ,$299.50", "$374.38 ,$0.00")
    res = run_build(tmp_path, src_dir=src_copy, settings=Settings(confirmed_zero_loss_severity="reject"))
    assert rejected_cases(res, "DQ-10") == {"FC0000002"}


def test_cases_opened_after_run_date_are_rejected(tmp_path):
    res = run_build(tmp_path, as_of=date(2026, 8, 15))
    rejected = rejected_cases(res, "DQ-11")
    assert rejected and len(rejected) + len(res.product) == 100
    assert all(ts.date() <= date(2026, 8, 15) for ts in res.product["case_open_ts"])
