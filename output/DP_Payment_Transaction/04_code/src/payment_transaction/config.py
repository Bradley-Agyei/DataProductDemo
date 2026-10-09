"""Paths for DP_Payment_Transaction. Change behaviour here, not in the logic."""
from pathlib import Path

from contracts.sources import SOURCES

CODE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_DIR.parents[2]

SOURCE_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = CODE_DIR / "payment_transaction.db"
OUT_DIR = CODE_DIR / "out"

SOURCE_FILES = {name: f"{name}.csv" for name in SOURCES}

# PII never leaves data/raw (CLAUDE.md). PRD §5.7 marks Member first_name, last_name,
# city and postal_code as PII; §5.5 hides Branch city and postal_code because they
# match member PII. These columns are header-checked and landed, but every value is
# replaced with PII_MASK; no Payment Transaction requirement uses them.
PII_MASK = "*"
PII_MASKED_COLUMNS: dict[str, tuple[str, ...]] = {
    "Branch": ("city", "postal_code"),
    "Member": ("first_name", "last_name", "city", "postal_code"),
}
