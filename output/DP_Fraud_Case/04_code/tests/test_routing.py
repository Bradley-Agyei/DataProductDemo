"""Optional queue routing check (DQ-13): off by default, warns without dropping cases when configured."""
from src.fraud_case.config import Settings
from tests.conftest import run_build

QUEUES_ALL = ("Deposit Ops", "Digital Fraud", "Enhanced Review", "Card Ops")


def dq13(res):
    return res.dq_results.set_index("rule_id").loc["DQ-13"]


def test_routing_check_off_by_default(result):
    rule = dq13(result)
    assert (rule["status"], rule["rows_checked"], rule["rows_failed"]) == ("Pass", 0, 0)


def test_routing_matrix_flags_unexpected_queue(tmp_path):
    res = run_build(tmp_path, settings=Settings(allowed_queues_by_case_type={"Card Fraud": ("Card Ops",)}))
    rule = dq13(res)
    # 20 Card Fraud cases; only the 5 in Card Ops (FC20, 40, 60, 80, 100) are allowed.
    assert (rule["status"], rule["rows_checked"], rule["rows_failed"]) == ("Warn", 100, 15)
    assert "FC0000005" in set(res.product["case_id"]) and len(res.product) == 100
    assert res.status == "SUCCESS"


def test_case_types_outside_matrix_are_not_checked(tmp_path):
    res = run_build(tmp_path, settings=Settings(allowed_queues_by_case_type={"Wire Fraud": QUEUES_ALL}))
    assert dq13(res)["rows_failed"] == 0
