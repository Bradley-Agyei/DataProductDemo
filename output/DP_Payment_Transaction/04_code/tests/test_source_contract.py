"""Source contracts and raw key integrity, checked against PRD_Payment_Transaction.md §5.

The expected columns are read from the PRD file itself, so a PRD change that the
contract does not follow fails here. data/raw is read-only: if a raw check fails,
the source changed and that is a finding for the source owner, not a file to fix.
Assertions report counts and key values only, never a PII value.
"""
import re
from datetime import datetime

import pandas as pd
import pytest

from contracts.sources import SOURCES
from src.payment_transaction import config

PRD = config.CODE_DIR.parent / "PRD_Payment_Transaction.md"
_SECTION = re.compile(r"^### 5\.\d+ .*\((\w+)\.csv\)")


def prd_source_tables() -> dict[str, list[tuple[str, str, str, str]]]:
    """PRD §5.x tables as {file stem: [(column, logical type, physical type, key)]}, keys as in the contract."""
    tables, current = {}, None
    for line in PRD.read_text(encoding="utf-8").splitlines():
        heading = _SECTION.match(line)
        if heading:
            current = tables.setdefault(heading.group(1), [])
            continue
        if line.startswith("#"):
            current = None
        if current is None or not line.startswith("| ") or line.startswith(("| Column", "|---")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        name, logical, physical, key = cells[0], cells[1], cells[2], cells[4]
        if key.startswith("FK → "):
            key = f"FK:{key[len('FK → '):]}.{name}"  # every PRD §5 FK names its parent's same-named column
        current.append((name, logical, physical, key))
    return tables


PRD_SOURCES = prd_source_tables()

# PRD §5 raw ID formats (before FR-02 conforms them).
RAW_ID_FORMATS = {
    ("Transaction", "transaction_id"): r"TXN\d{6}", ("Transaction", "account_id"): r"A\d{5}",
    ("Transaction", "member_id"): r"M\d{4}", ("Transaction", "transaction_type_id"): r"TT\d{2}",
    ("Transaction", "channel_id"): r"C\d{2}", ("Transaction", "branch_id"): r"B\d{3}",
    ("Transaction", "date_key"): r"\d{8}", ("Transaction", "reference_number"): r"REF\d{9}",
    ("Transaction_Type", "transaction_type_id"): r"TT\d{2}", ("Channel", "channel_id"): r"C\d{2}",
    ("Date", "date_key"): r"\d{8}", ("Branch", "branch_id"): r"B\d{3}",
    ("Account", "account_id"): r"A\d{5}", ("Account", "member_id"): r"M\d{4}",
    ("Account", "product_id"): r"P\d{3}", ("Account", "branch_id"): r"B\d{3}",
    ("Member", "member_id"): r"M\d{4}",
}


def raw(name):
    df = pd.read_csv(config.SOURCE_DIR / f"{name}.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return df.apply(lambda s: s.str.strip())


def primary_key(name):
    keys = [c.name for c in SOURCES[name].columns if c.key == "PK"]
    assert len(keys) == 1, f"{name} contract must have exactly one PK column, has {keys}"
    return keys[0]


def test_prd_lists_every_source():
    """§5.8 (account_id_map) is a reference table, not one of the 7 ingested sources."""
    assert sorted(set(PRD_SOURCES) - {"account_id_map"}) == sorted(SOURCES)


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_source_contract_matches_prd(name):
    expected = [(column, physical, key) for column, _, physical, key in PRD_SOURCES[name]]
    actual = [(c.name, c.type, c.key) for c in SOURCES[name].columns]
    assert actual == expected


def test_member_pii_columns_are_masked():
    prd_pii = {column for column, logical, _, _ in PRD_SOURCES["Member"] if logical == "PII"}
    assert prd_pii == {"first_name", "last_name", "city", "postal_code"}
    assert set(config.PII_MASKED_COLUMNS["Member"]) == prd_pii


def test_branch_columns_hidden_in_prd_are_masked():
    """PRD §5.5 hides Branch city and postal_code as matching member PII."""
    hidden = {column for column, *_ in PRD_SOURCES["Branch"]} & {"city", "postal_code"}
    assert set(config.PII_MASKED_COLUMNS["Branch"]) == hidden == {"city", "postal_code"}


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_raw_primary_key_unique_and_present(name):
    key = raw(name)[primary_key(name)]
    assert (key == "").sum() == 0
    assert key.duplicated().sum() == 0


@pytest.mark.parametrize("table, column", sorted(RAW_ID_FORMATS))
def test_raw_ids_match_prd_format(table, column):
    values = raw(table)[column]
    bad = sorted(set(values[~values.str.fullmatch(RAW_ID_FORMATS[(table, column)])]))
    assert bad == []


FOREIGN_KEYS = sorted((t, c.name, *c.foreign_key) for t in SOURCES for c in SOURCES[t].columns if c.foreign_key)


@pytest.mark.parametrize("table, column, parent, parent_column", FOREIGN_KEYS)
def test_raw_foreign_keys_resolve(table, column, parent, parent_column):
    """Includes Account.product_id -> Product.csv, which Payment Transaction reads only for this check."""
    orphans = sorted(set(raw(table)[column]) - set(raw(parent)[parent_column]))
    assert orphans == []


def test_date_key_matches_full_date():
    dates = raw("Date")
    as_key = dates["full_date"].map(lambda d: datetime.strptime(d, "%m/%d/%Y").strftime("%Y%m%d"))
    assert (as_key == dates["date_key"]).all()


def test_transaction_matches_account_owner_and_branch():
    """PRD §5.1: member and branch match the account on every row (DQ-09 guards it in FR-04)."""
    transactions = raw("Transaction")
    txn = transactions.merge(raw("Account")[["account_id", "member_id", "branch_id"]],
                             on="account_id", suffixes=("", "_account"))
    assert len(txn) == len(transactions)
    assert (txn["member_id"] == txn["member_id_account"]).all()
    assert (txn["branch_id"] == txn["branch_id_account"]).all()


def test_transaction_direction_matches_type():
    """PRD §5.1: debit_credit_indicator matches Transaction_Type on every row (DQ-07 in FR-04)."""
    transactions = raw("Transaction")
    txn = transactions.merge(raw("Transaction_Type")[["transaction_type_id", "debit_credit_indicator"]],
                             on="transaction_type_id", suffixes=("", "_type"))
    assert len(txn) == len(transactions)
    assert (txn["debit_credit_indicator"] == txn["debit_credit_indicator_type"]).all()


def test_every_account_is_in_account_id_map():
    ref = pd.read_csv(config.PROJECT_ROOT / "data" / "reference" / "account_id_map.csv", dtype=str,
                      keep_default_na=False)
    core = set(ref.loc[ref["source_system"] == "core_banking", "source_account_id"])
    assert set(raw("Account")["account_id"]) <= core
