"""Data quality rules, publish gating and the exception report."""
import sqlite3

import pandas as pd
import pytest

from src.member_360 import config
from src.member_360 import run as run_module
from tests.conftest import edit_csv, run_build

ALL_RULES = {f"DQ-{n:02d}" for n in range(1, 12)}


def test_every_rule_runs_and_is_recorded(result):
    assert set(result.dq_results["rule_id"]) == ALL_RULES
    with sqlite3.connect(result.db_path) as conn:
        stored = {r[0] for r in conn.execute("SELECT rule_id FROM dq_results WHERE dp_batch_id = 'test-batch'")}
    assert stored == ALL_RULES


def test_sample_passes_all_rules(result):
    assert result.status == "SUCCESS"
    assert set(result.dq_results["status"]) == {"Pass"}


def test_foreign_key_failures_cascade_to_transactions(tmp_path, src_copy):
    edit_csv(src_copy / "Account.csv", "A00001,M0001,P001,B001", "A00001,M0001,P999,B001")
    res = run_build(tmp_path, src_dir=src_copy)
    reasons = res.rejects.groupby("table_name")["reason"].first()
    assert reasons["Account"].startswith("DQ-09")
    assert (res.rejects["table_name"] == "Transaction").sum() == 10
    assert res.status == "SUCCESS"


def test_sample_accounts_are_all_mapped(result):
    dq11 = result.dq_results.set_index("rule_id").loc["DQ-11"]
    assert (dq11["status"], dq11["rows_checked"]) == ("Pass", 10)


def test_account_missing_from_reference_table_is_rejected(tmp_path):
    ref = tmp_path / "account_id_map.csv"
    lines = config.ACCOUNT_REFERENCE_CSV.read_text(encoding="utf-8").splitlines(keepends=True)
    ref.write_text("".join(l for l in lines if not l.startswith("core_banking,A00001,")), encoding="utf-8")
    res = run_build(tmp_path, account_ref=ref)
    account_rejects = res.rejects[res.rejects["table_name"] == "Account"]
    assert account_rejects["row_key"].tolist() == ["A00001"]
    assert account_rejects["reason"].iloc[0].startswith("DQ-11")
    txn_rejects = res.rejects[res.rejects["table_name"] == "Transaction"]
    assert len(txn_rejects) == 10 and txn_rejects["reason"].str.startswith("DQ-09").all()


def test_missing_reference_table_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError, match="account ID mapping reference table"):
        run_build(tmp_path, account_ref=tmp_path / "nope.csv")


def test_future_join_date_rejects_member_row(tmp_path, src_copy):
    edit_csv(src_copy / "Member.csv", "10/14/2021", "1/1/2030")
    res = run_build(tmp_path, src_dir=src_copy)
    assert "M000010" not in set(res.product["member_id"])
    assert res.rejects.query("table_name == 'member_360'")["reason"].str.startswith("DQ-05").all()
    assert res.status == "SUCCESS"


def test_blocking_failure_keeps_previous_product(tmp_path, monkeypatch):
    run_build(tmp_path)
    real_build = run_module.build_member_360

    def duplicated(*args, **kwargs):
        product, xref = real_build(*args, **kwargs)
        return pd.concat([product, product.head(1)], ignore_index=True), xref

    monkeypatch.setattr(run_module, "build_member_360", duplicated)
    res = run_build(tmp_path, batch_id="bad-batch")

    assert res.status == "BLOCKED"
    dq01 = res.dq_results.set_index("rule_id").loc["DQ-01"]
    assert dq01["status"] == "Fail" and dq01["rows_failed"] == 2
    with sqlite3.connect(tmp_path / "member_360.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM member_360").fetchone()[0] == 10
        assert conn.execute("SELECT COUNT(*) FROM member_360 WHERE dp_batch_id = 'bad-batch'").fetchone()[0] == 0


def test_exception_report(result):
    exc = result.exceptions
    negative = exc[exc["exception_type"] == "NEGATIVE_BALANCE"]
    assert set(negative["transaction_id"]) == {"TXN000023", "TXN000073"}
    assert set(negative["account_id"]) == {"A00003"}
    dormant = exc[exc["exception_type"] == "DORMANT_RESTRICTED_ACTIVITY"]
    assert len(dormant) == 20
    assert set(dormant["member_id"]) == {"M000004", "M000008"}


def test_run_log_reconciles(result):
    log = result.run_log.set_index("table_name")
    assert log.loc["stg_transaction", ["rows_in", "rows_out", "rows_rejected"]].tolist() == [100, 100, 0]
    assert log.loc["member_360", ["rows_in", "rows_out", "status"]].tolist() == [10, 10, "SUCCESS"]
