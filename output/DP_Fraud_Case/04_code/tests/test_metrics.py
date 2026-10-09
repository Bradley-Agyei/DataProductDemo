"""Derived case metrics and the critical-case aging exception."""
from datetime import date, datetime
from decimal import Decimal

from src.fraud_case.config import Settings
from src.fraud_case.transform import case_age_days, days_to_close, loss_confirmation_ratio
from tests.conftest import by_case, run_build


def test_days_to_close():
    assert days_to_close(datetime(2026, 8, 1, 16), datetime(2026, 8, 4, 16)) == Decimal("3.00")
    assert days_to_close(datetime(2026, 8, 1, 8), datetime(2026, 8, 1, 20)) == Decimal("0.50")
    assert days_to_close(datetime(2026, 8, 1, 8), None) is None


def test_case_age_days():
    assert case_age_days(datetime(2026, 8, 1, 8), False, date(2026, 10, 4)) == 63
    assert case_age_days(datetime(2026, 8, 1, 8), True, date(2026, 10, 4)) is None


def test_loss_confirmation_ratio():
    assert loss_confirmation_ratio(Decimal("299.50"), Decimal("374.38"), True) == Decimal("0.8000")
    assert loss_confirmation_ratio(Decimal("0"), Decimal("511.57"), True) == Decimal("0.0000")
    assert loss_confirmation_ratio(Decimal("10"), Decimal("0"), True) is None
    assert loss_confirmation_ratio(Decimal("10"), Decimal("20"), False) is None


def test_known_cases(result):
    rows = by_case(result.product)
    assert rows.loc["FC0000002", ["is_closed", "days_to_close", "loss_confirmation_ratio"]].tolist() == \
        [True, Decimal("3.00"), Decimal("0.8000")]
    assert rows.loc["FC0000001", ["is_closed", "case_age_days"]].tolist() == [False, 63]


def test_metrics_null_by_lifecycle(result):
    for r in result.product.to_dict("records"):
        if r["is_closed"]:
            assert r["case_age_days"] is None and r["days_to_close"] is not None
        else:
            assert r["days_to_close"] is None and r["loss_confirmation_ratio"] is None
            assert r["case_age_days"] is not None


def test_sample_metric_ranges(result):
    p = result.product
    closed = p[p["is_closed"] == True]  # noqa: E712
    assert len(closed) == 40
    assert min(closed["days_to_close"]) == Decimal("1.00") and max(closed["days_to_close"]) == Decimal("12.00")
    confirmed = closed[closed["resolution_code"] == "Confirmed Fraud"]["loss_confirmation_ratio"]
    assert len(confirmed) == 27
    assert min(confirmed) == Decimal("0.3500") and max(confirmed) == Decimal("0.8000")
    assert set(closed[closed["resolution_code"] == "False Positive"]["loss_confirmation_ratio"]) == {Decimal("0.0000")}


def breached(res):
    return res.exceptions[res.exceptions["exception_type"] == "CASE_SLA_BREACHED"]


def test_sla_days_by_priority(result):
    sla = dict(zip(result.product["priority"], result.product["sla_days"]))
    assert sla == {"Critical": 30, "High": 45, "Medium": 60, "Low": 90}


def test_sla_breached_flag(result):
    rows = by_case(result.product)
    assert rows.loc["FC0000011", "sla_breached_flag"] is True      # Critical, open 60 days
    assert rows.loc["FC0000002", "sla_breached_flag"] is False     # High, closed in 3 days
    assert rows.loc["FC0000054", "sla_breached_flag"] is True      # High, open exactly 46 days
    assert rows.loc["FC0000058", "sla_breached_flag"] is False     # High, closed in 11 days


def test_open_breaches_reported_by_priority(result):
    # Hand count at 2026-10-04: Critical 15 (all open > 30 days), High 9 (FC6..FC54),
    # Medium 3 (FC1, FC5, FC9), Low 0 (oldest open case is 63 days).
    rows = by_case(result.product)
    exc = breached(result)
    by_priority = exc["case_id"].map(rows["priority"]).value_counts().to_dict()
    assert by_priority == {"Critical": 15, "High": 9, "Medium": 3}
    assert not any(rows.loc[c, "is_closed"] for c in exc["case_id"])


def test_closed_cases_within_sla(result):
    closed = result.product[result.product["is_closed"] == True]  # noqa: E712
    assert not any(closed["sla_breached_flag"])


def test_former_critical_only_exception_is_gone(result):
    assert "CRITICAL_CASE_AGED" not in set(result.exceptions["exception_type"])


def test_sla_days_are_configurable(tmp_path):
    sla = {"Critical": 45, "High": 45, "Medium": 60, "Low": 90}
    res = run_build(tmp_path, settings=Settings(sla_days_by_priority=sla))
    rows = by_case(res.product)
    critical = {c for c in breached(res)["case_id"] if rows.loc[c, "priority"] == "Critical"}
    assert critical == {"FC0000011", "FC0000015", "FC0000019", "FC0000031", "FC0000035", "FC0000039", "FC0000051"}
