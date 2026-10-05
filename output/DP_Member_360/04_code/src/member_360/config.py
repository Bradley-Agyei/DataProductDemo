"""Paths, business switches and reference lists for Member 360. Change behaviour here, not in the logic."""
from dataclasses import dataclass, field
from pathlib import Path

from contracts.sources import SOURCES

CODE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_DIR.parents[2]

SOURCE_DIR = PROJECT_ROOT / "data" / "raw"
SAMPLE_PRODUCT_CSV = PROJECT_ROOT / "data" / "product" / "DP_Member_360.csv"
# Shared account ID mapping reference table (built by tools/build_account_id_map.py).
ACCOUNT_REFERENCE_CSV = PROJECT_ROOT / "data" / "reference" / "account_id_map.csv"
CORE_BANKING_SYSTEM = "core_banking"
DB_PATH = CODE_DIR / "member_360.db"
OUT_DIR = CODE_DIR / "out"
DDL_DIR = CODE_DIR / "sql" / "ddl"

SOURCE_FILES = {name: f"{name}.csv" for name in SOURCES}

# (min age, max age or None, label); under 18 has no band.
AGE_BANDS = (
    (18, 24, "18-24"), (25, 34, "25-34"), (35, 44, "35-44"),
    (45, 54, "45-54"), (55, 64, "55-64"), (65, None, "65+"),
)

US_STATES = frozenset("""
    AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY
    NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY
""".split())

CONTRACT_META = {
    "version": "0.1",
    "owner": "Product Owner - Member Data",
    "refresh": "Daily full rebuild, ready by 07:00 ET",
    "change_policy": "New columns are additive; type changes need 30 days' notice",
    "source_prd": "output/DP_Member_360/PRD_Member_360.md",
    "jira": "SCRUM-17",
}


@dataclass(frozen=True)
class Settings:
    id_width: int = 6
    source_system: str = "core_csv"
    # Pending PO approval: a member with any Restricted account is Restricted overall.
    restricted_rule: bool = True
    # Interim stand-in until the digital-banking enrollment feed exists.
    digital_proxy: bool = False
    digital_channels: frozenset = field(default_factory=lambda: frozenset({"C03", "C04"}))
    digital_lookback_days: int = 90
