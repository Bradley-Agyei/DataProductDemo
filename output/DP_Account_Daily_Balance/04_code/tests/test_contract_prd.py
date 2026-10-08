"""The account_daily_balance contract checked against PRD_Account_Daily_Balance.md §6.

The expected columns are read from the PRD file itself, so a PRD change that the
contract does not follow fails here.
"""
from contracts.account_daily_balance import ACCOUNT_DAILY_BALANCE
from src.account_daily_balance import config

PRD = config.CODE_DIR.parent / "PRD_Account_Daily_Balance.md"


def prd_target_columns() -> list[dict]:
    """Rows of the §6 target table as {column, physical, key, allowed}."""
    rows, in_section = [], False
    for line in PRD.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.startswith("## 6. ")
            continue
        if not in_section or not line.startswith("| ") or line.startswith(("| Column", "|---")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append({"column": cells[0], "physical": cells[2], "key": cells[4], "allowed": cells[5]})
    return rows


PRD_COLUMNS = prd_target_columns()


def test_columns_and_types_follow_prd_order():
    assert [(r["column"], r["physical"]) for r in PRD_COLUMNS] == \
        [(c.name, c.type) for c in ACCOUNT_DAILY_BALANCE.columns]


def test_primary_key_matches_prd():
    """PRD writes the key as (account_id, balance_date); the DDL lists it in column order."""
    assert {r["column"] for r in PRD_COLUMNS if r["key"] == "PK"} == set(ACCOUNT_DAILY_BALANCE.primary_key) \
        == {"account_id", "balance_date"}


def test_category_allowed_values_match_prd():
    for name in ("product_code", "account_status"):
        prd = next(r for r in PRD_COLUMNS if r["column"] == name)
        assert tuple(v.strip() for v in prd["allowed"].split(",")) == ACCOUNT_DAILY_BALANCE.column(name).allowed


def test_sample_columns_are_the_first_eleven_prd_columns():
    """PRD §6: column order is the 11 sample columns, then derived, then audit."""
    assert list(config.SAMPLE_COLUMNS) == [r["column"] for r in PRD_COLUMNS[:11]]
