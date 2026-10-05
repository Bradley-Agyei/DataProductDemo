"""Core product columns built from today's sources."""
from datetime import date

from contracts.member_360 import MEMBER_360
from src.member_360.config import Settings
from tests.conftest import run_build


def by_id(product):
    return product.set_index("member_id")


def test_one_row_per_source_member(result):
    assert len(result.product) == 10
    assert result.product["member_id"].is_unique


def test_columns_follow_contract_order(result):
    assert list(result.product.columns) == MEMBER_360.column_names


def test_restricted_account_makes_relationship_restricted(result):
    status = by_id(result.product)["relationship_status"]
    assert status["M000004"] == "Restricted"
    assert status["M000008"] == "Restricted"
    others = status.drop(["M000004", "M000008"])
    assert set(others) == {"Active"}


def test_restricted_rule_can_be_switched_off(tmp_path):
    res = run_build(tmp_path, settings=Settings(restricted_rule=False))
    status = by_id(res.product)["relationship_status"]
    assert status["M000004"] == "Dormant"
    assert status["M000008"] == "Dormant"


def test_direct_mappings(result):
    row = by_id(result.product).loc["M000010"]
    assert row["home_state"] == "NC"
    assert row["member_since_date"] == date(2021, 10, 14)
    assert row["member_segment"] == "Premium"


def test_audit_columns_populated(result):
    assert set(result.product["dp_batch_id"]) == {"test-batch"}
    assert result.product["dp_load_ts"].notna().all()


def test_no_pii_in_product(result):
    assert not {"first_name", "last_name", "postal_code"} & set(result.product.columns)
