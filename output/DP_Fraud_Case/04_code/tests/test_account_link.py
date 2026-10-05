"""Account link through the shared account ID mapping reference table: kept, flagged and reported."""
import pytest

from tests.conftest import ACCOUNT_REF, by_case, run_build


def test_account_found_flag(result):
    flags = by_case(result.product)["account_found_flag"]
    assert flags["FC0000001"] is True       # A0000001 -> core banking A00001
    assert flags["FC0000010"] is True
    assert flags["FC0000011"] is False      # A0000011 has no core banking account
    assert sum(1 for f in flags if f is True) == 10


def test_unmatched_accounts_are_kept_and_reported(result):
    missing = result.exceptions[result.exceptions["exception_type"] == "ACCOUNT_NOT_FOUND"]
    assert len(missing) == 90 and len(result.product) == 100
    assert "FC0000001" not in set(missing["case_id"])


def test_account_unknown_to_reference_table_is_not_found(tmp_path):
    ref = tmp_path / "account_id_map.csv"
    lines = ACCOUNT_REF.read_text(encoding="utf-8").splitlines(keepends=True)
    ref.write_text("".join(l for l in lines if not l.startswith("fraud_case_mgmt,A0000001,")), encoding="utf-8")
    res = run_build(tmp_path, account_ref=ref)
    assert by_case(res.product).loc["FC0000001", "account_found_flag"] is False


def test_missing_reference_table_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError, match="account ID mapping reference table not found"):
        run_build(tmp_path, account_ref=tmp_path / "nope.csv")
