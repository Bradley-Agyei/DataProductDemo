"""FR-06 (SCRUM-42): account attributes, product code lookup, DQ-13 and DQ-14."""
from datetime import date
from decimal import Decimal as D

import pandas as pd
import pytest

from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE, PRODUCT_CODES
from contracts.sources import PRODUCT_CODE_REF
from src.account_daily_balance.attributes import account_attributes, dormant_activity, load_product_code_ref

DAYS = [date(2026, 9, 21), date(2026, 9, 22)]
PII = ("first_name", "last_name", "postal_code")


def make_balances(account_ids=("A0000001", "A0000002")) -> pd.DataFrame:
    return pd.DataFrame([{"balance_date": d, "account_id": a, "opening_balance": D("1.00"),
                          "total_credits": D("0.00"), "total_debits": D("0.00"), "closing_balance": D("1.00")}
                         for a in account_ids for d in DAYS], dtype=object)


def make_accounts(rows=None) -> pd.DataFrame:
    rows = rows or [("A0000001", "M000001", "P001", "Open"), ("A0000002", "M000002", "P002", "Restricted")]
    return pd.DataFrame(rows, columns=["account_id", "member_id", "product_id", "account_status"], dtype=object)


def make_ref(rows=(("P001", "CHK_STD"), ("P002", "CHK_REW"))) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=["product_id", "product_code"], dtype=object)


def write_ref(tmp_path, text: str):
    path = tmp_path / "product_code_map.csv"
    path.write_text(text, encoding="utf-8")
    return path


# 1.1 reference table contract

def test_product_code_ref_shares_allowed_codes():
    assert PRODUCT_CODE_REF.column("product_code").allowed == PRODUCT_CODES \
        == ACCOUNT_DAILY_BALANCE.column("product_code").allowed
    assert PRODUCT_CODE_REF.primary_key == ["product_id"]


# 1.2 loading the reference table

def test_ref_absent_returns_none(tmp_path):
    assert load_product_code_ref(tmp_path / "missing.csv") is None


def test_ref_valid_loads(tmp_path):
    ref = load_product_code_ref(write_ref(tmp_path, "product_id,product_code\nP001,CHK_STD\nP010,CC_REW\n"))
    assert dict(zip(ref["product_id"], ref["product_code"])) == {"P001": "CHK_STD", "P010": "CC_REW"}


def test_ref_duplicate_product_id_raises(tmp_path):
    with pytest.raises(ValueError, match="P001"):
        load_product_code_ref(write_ref(tmp_path, "product_id,product_code\nP001,CHK_STD\nP001,CHK_REW\n"))


def test_ref_code_not_allowed_raises(tmp_path):
    with pytest.raises(ValueError, match="CHK_GOLD"):
        load_product_code_ref(write_ref(tmp_path, "product_id,product_code\nP011,CHK_GOLD\n"))


def test_ref_missing_value_raises(tmp_path):
    with pytest.raises(ValueError, match="P002"):
        load_product_code_ref(write_ref(tmp_path, "product_id,product_code\nP001,CHK_STD\nP002,\n"))


# 2.1 attributes on every row

def test_status_copied_to_every_day():
    rows, _ = account_attributes(make_balances(), make_accounts())
    by_account = rows.groupby("account_id")["account_status"].agg(set).to_dict()
    assert by_account == {"A0000001": {"Open"}, "A0000002": {"Restricted"}}
    assert len(rows) == 4


def test_member_id_conformed():
    rows, _ = account_attributes(make_balances(), make_accounts())
    assert set(rows.loc[rows["account_id"] == "A0000001", "member_id"]) == {"M000001"}


def test_product_code_from_ref():
    rows, warnings = account_attributes(make_balances(), make_accounts(), make_ref())
    assert set(rows.loc[rows["account_id"] == "A0000001", "product_code"]) == {"CHK_STD"}
    assert set(rows.loc[rows["account_id"] == "A0000002", "product_code"]) == {"CHK_REW"}
    assert warnings == []
    assert "product_id" not in rows.columns


def test_product_code_follows_ref_not_code():
    rows, _ = account_attributes(make_balances(), make_accounts(), make_ref([("P001", "CHK_REW"), ("P002", "MMA")]))
    assert set(rows.loc[rows["account_id"] == "A0000001", "product_code"]) == {"CHK_REW"}


def test_product_code_null_without_ref():
    rows, warnings = account_attributes(make_balances(), make_accounts())
    assert rows["product_code"].map(lambda v: v is None).all()
    assert warnings == []


def test_columns_follow_contract_order():
    rows, _ = account_attributes(make_balances(), make_accounts())
    contract = [c for c in ACCOUNT_DAILY_BALANCE.column_names if c in rows.columns]
    assert list(rows.columns) == contract


def test_balance_without_account_raises():
    with pytest.raises(ValueError, match="A0000002"):
        account_attributes(make_balances(), make_accounts([("A0000001", "M000001", "P001", "Open")]))


# 2.2 DQ-14

def test_unmatched_product_warns_dq14():
    accounts = make_accounts([("A0000001", "M000001", "P001", "Open"), ("A0000002", "M000002", "P010", "Open")])
    rows, warnings = account_attributes(make_balances(), accounts, make_ref())
    assert rows.loc[rows["account_id"] == "A0000002", "product_code"].map(lambda v: v is None).all()
    assert [(w["exception_type"], w["rule_id"], w["row_key"]) for w in warnings] == [("WARN", "DQ-14", "A0000002")]


def test_null_product_id_warns_dq14():
    accounts = make_accounts([("A0000001", "M000001", "P001", "Open"), ("A0000002", "M000002", None, "Open")])
    _, warnings = account_attributes(make_balances(), accounts, make_ref())
    assert [w["row_key"] for w in warnings] == ["A0000002"]


def test_no_dq14_without_ref():
    accounts = make_accounts([("A0000001", "M000001", "P099", "Open"), ("A0000002", "M000002", "P098", "Open")])
    assert account_attributes(make_balances(), accounts)[1] == []


# 2.3 DQ-13

def members(*rows) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=["member_id", "member_status"], dtype=object)


def transactions(*account_ids) -> pd.DataFrame:
    return pd.DataFrame({"account_id": list(account_ids),
                         "transaction_status": ["Pending"] * len(account_ids)}, dtype=object)


def test_dormant_pending_only_is_reported():
    accounts = make_accounts([("A0000004", "M000004", "P004", "Restricted")])
    warnings = dormant_activity(accounts, members(("M000004", "Dormant")), transactions("A0000004", "A0000004"))
    assert [(w["exception_type"], w["rule_id"], w["row_key"]) for w in warnings] == [("WARN", "DQ-13", "M000004")]
    assert warnings[0]["detail"] == "Dormant member with activity: 2 transactions on 1 account"


def test_dormant_with_open_account_is_reported():
    accounts = make_accounts([("A0000001", "M000001", "P001", "Open")])
    warnings = dormant_activity(accounts, members(("M000001", "Dormant")), transactions("A0000001"))
    assert [w["row_key"] for w in warnings] == ["M000001"]


def test_active_member_restricted_account_not_reported():
    accounts = make_accounts([("A0000002", "M000002", "P002", "Restricted")])
    assert dormant_activity(accounts, members(("M000002", "Active")), transactions("A0000002")) == []


def test_dormant_without_activity_not_reported():
    accounts = make_accounts([("A0000001", "M000001", "P001", "Open"), ("A0000002", "M000002", "P002", "Open")])
    assert dormant_activity(accounts, members(("M000001", "Dormant")), transactions("A0000002")) == []


def test_dormant_reported_once_across_accounts_and_days():
    accounts = make_accounts([("A0000001", "M000001", "P001", "Open"), ("A0000002", "M000001", "P002", "Open")])
    warnings = dormant_activity(accounts, members(("M000001", "Dormant")),
                                transactions("A0000001", "A0000001", "A0000002"))
    assert [w["row_key"] for w in warnings] == ["M000001"]
    assert warnings[0]["detail"] == "Dormant member with activity: 3 transactions on 2 accounts"


def test_dormant_detail_has_no_pii():
    """Even when PII columns reach the members frame, none of their values is written."""
    accounts = make_accounts([("A0000001", "M000001", "P001", "Open")])
    member_frame = members(("M000001", "Dormant")).assign(first_name="Zelda", last_name="Quorn", postal_code="99999")
    warnings = dormant_activity(accounts, member_frame, transactions("A0000001"))
    text = " ".join(str(v) for w in warnings for v in w.values())
    assert not any(v in text for v in ("Zelda", "Quorn", "99999"))
    assert not any(name in text for name in PII)


# --- sample acceptance (Jira SCRUM-42) ---

def test_sample_member_loader_reads_no_pii_columns():
    from tests.sample_inputs import load_members
    assert list(load_members().columns) == ["member_id", "member_status"]


@pytest.fixture(scope="module")
def sample_run(tmp_path_factory):
    """Sample sources -> roll-forward -> FR-06 -> publish, with no product code reference table.

    available_balance and pending_debits stand in for FR-05 and FR-03 (not built yet).
    """
    from src.account_daily_balance.roll_forward import roll_forward
    from tests.conftest import run_publish
    from tests.sample_inputs import load_account_attributes, load_activity, load_members, load_sample

    accounts, dates, totals = load_sample()
    balances = roll_forward(accounts, dates, totals).assign(available_balance=None, pending_debits=D("0.00"))
    balances["overdraft_flag"] = balances["closing_balance"].map(lambda v: v < 0)
    attrs = load_account_attributes()
    product, product_warnings = account_attributes(balances, attrs, product_ref=None)
    warnings = product_warnings + dormant_activity(attrs, load_members(), load_activity())
    counted = pd.concat([totals.assign(signed_amount=totals["total_credits"]),
                         totals.assign(signed_amount=-totals["total_debits"])])[["account_id", "signed_amount"]]
    return run_publish(tmp_path_factory.mktemp("sample"), product=product, counted=counted,
                       upstream_warnings=warnings)


# AC: Dormant members M000004 and M000008 reported in the exception report (DQ-13)
def test_sample_dormant_members_reported(sample_run):
    dq13 = sample_run.exceptions[sample_run.exceptions["rule_id"] == "DQ-13"]
    assert sorted(dq13["row_key"]) == ["M000004", "M000008"]
    assert set(dq13["exception_type"]) == {"WARN"}


# AC: account_status is one of Open, Restricted (DQ-04)
def test_sample_account_status_values(sample_run):
    product = sample_run.product
    per_account = product.groupby("account_id")["account_status"].agg(set)
    assert per_account.map(len).eq(1).all()
    assert per_account.map(lambda s: next(iter(s))).value_counts().to_dict() == {"Open": 8, "Restricted": 2}
    dq04 = sample_run.dq_results.set_index("rule_id").loc["DQ-04"]
    assert dq04["rows_failed"] == 0


# AC: product_code pending until Q6 - NULL everywhere, run not blocked, no DQ-14
def test_sample_product_code_pending(sample_run):
    assert sample_run.status == "SUCCESS"
    assert len(sample_run.product) == 100
    assert sample_run.product["product_code"].map(lambda v: v is None or pd.isna(v)).all()
    assert "DQ-14" not in set(sample_run.exceptions["rule_id"])
