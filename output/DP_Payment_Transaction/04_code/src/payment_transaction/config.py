"""Paths for DP_Payment_Transaction. Change behaviour here, not in the logic."""
from pathlib import Path

from contracts.sources import SOURCES

CODE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_DIR.parents[2]

SOURCE_DIR = PROJECT_ROOT / "data" / "raw"
# The raw layer holds Member PII as received, so it is written only to git-ignored paths.
DB_PATH = CODE_DIR / "payment_transaction.db"
OUT_DIR = CODE_DIR / "out"

SOURCE_FILES = {name: f"{name}.csv" for name in SOURCES}
