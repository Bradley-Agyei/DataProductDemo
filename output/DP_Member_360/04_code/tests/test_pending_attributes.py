"""Columns waiting on new feeds: published as NULL, typed, and ready to switch on."""
from datetime import date

import pytest

from contracts.member_360 import MEMBER_360
from src.member_360.config import Settings
from src.member_360.transform import age_band
from tests.conftest import run_build

PENDING = ["age_band", "digital_enrolled_flag", "kyc_status", "risk_rating", "last_profile_update_ts"]


def test_contract_marks_feed_columns_pending():
    assert [c.name for c in MEMBER_360.columns if c.is_pending] == PENDING


def test_pending_columns_are_null(result):
    for name in PENDING:
        assert result.product[name].isna().all(), name


def test_not_null_check_skips_pending_columns(result):
    dq03 = result.dq_results.set_index("rule_id").loc["DQ-03"]
    assert dq03["status"] == "Pass"


@pytest.mark.parametrize("birth, expected", [
    (date(2008, 10, 4), "18-24"),
    (date(2008, 10, 5), None),
    (date(1990, 1, 1), "35-44"),
    (date(1961, 10, 4), "65+"),
    (date(1961, 10, 5), "55-64"),
])
def test_age_band(birth, expected):
    assert age_band(birth, as_of=date(2026, 10, 4)) == expected


def test_digital_proxy_uses_recent_online_or_mobile_activity(tmp_path):
    res = run_build(tmp_path, settings=Settings(digital_proxy=True))
    flags = res.product.set_index("member_id")["digital_enrolled_flag"]
    assert flags["M000004"] is True      # Online Banking
    assert flags["M000007"] is True      # Mobile App
    assert not any(flags.drop(["M000004", "M000007"]))


def test_digital_proxy_ignores_activity_outside_lookback(tmp_path):
    res = run_build(tmp_path, as_of=date(2027, 6, 1), settings=Settings(digital_proxy=True))
    assert not any(res.product["digital_enrolled_flag"])
