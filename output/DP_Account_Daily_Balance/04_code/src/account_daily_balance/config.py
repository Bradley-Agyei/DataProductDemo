"""Paths and publish settings for Account Daily Balance. Change behaviour here, not in the logic."""
import re
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_DIR.parents[2]

# The target sample is shape only (PRD Q1) and not committed yet; the PRD names it
# data/output/product/, this repo keeps samples in data/product/. When it lands,
# the CSV header test compares against it instead of SAMPLE_COLUMNS (PRD §6 order).
SAMPLE_PRODUCT_CSV = PROJECT_ROOT / "data" / "product" / "DP_Account_Daily_Balance.csv"
SAMPLE_COLUMNS = ("balance_date", "account_id", "member_id", "product_code", "account_status",
                  "opening_balance", "total_credits", "total_debits", "closing_balance",
                  "available_balance", "overdraft_flag")

DB_PATH = CODE_DIR / "account_daily_balance.db"
OUT_DIR = CODE_DIR / "out"
DDL_DIR = CODE_DIR / "sql" / "ddl"

# PII never leaves data/raw (CLAUDE.md). Any column whose name normalizes to one of
# these is masked with PII_MASK before anything is written; matches the pii gate.
PII_MASK = "*"
PII_COLUMN_NAMES = frozenset({
    "firstname", "lastname", "postalcode",
    "fname", "lname", "givenname", "surname", "fullname",
    "zip", "zipcode", "postcode",
    "address", "addressline1", "addressline2", "streetaddress",
})


def is_pii_column(name: str) -> bool:
    return re.sub(r"[^a-z0-9]", "", str(name).lower()) in PII_COLUMN_NAMES


# Balances are DECIMAL(15,2); equality checks allow half a cent for float inputs.
AMOUNT_TOLERANCE = 0.005

# FR-04 (Q2, open: Finance confirm): the first day opens at this Account column.
# current_balance is the balance before the first sample transaction on 10 of 10 accounts.
FIRST_DAY_OPENING_COLUMN = "current_balance"

CONTRACT_META = {
    "version": "0.1",
    "owner": "Product Owner - Finance & Reporting Data",
    "refresh": "Daily full rebuild, ready by 07:00 ET",
    "change_policy": "New columns are additive; type changes need 30 days' notice",
    "source_prd": "output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md",
    "jira": "SCRUM-35 (FR-04: SCRUM-40, FR-07: SCRUM-43)",
    "pii": "None published; any PII value is masked with * before write",
}
