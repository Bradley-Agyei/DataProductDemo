"""Paths and business switches for Fraud Case. Change behaviour here, not in the logic."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

CODE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CODE_DIR.parents[2]

# The extract is not a data/raw feed (data/raw is read-only and owned upstream); the only
# committed copy is the byte-identical sample in data/product. Override with --src.
SOURCE_DIR = PROJECT_ROOT / "data" / "product"
SAMPLE_PRODUCT_CSV = PROJECT_ROOT / "data" / "product" / "DP_Fraud_Case.csv"
# Member 360 publishes this file; override with --member-ref.
MEMBER_REFERENCE_CSV = PROJECT_ROOT / "output" / "DP_Member_360" / "04_code" / "out" / "member_360.csv"
# Shared account ID mapping reference table (built by tools/build_account_id_map.py); override with --account-ref.
ACCOUNT_REFERENCE_CSV = PROJECT_ROOT / "data" / "reference" / "account_id_map.csv"
ACCOUNT_SOURCE_SYSTEM = "fraud_case_mgmt"
DB_PATH = CODE_DIR / "fraud_case.db"
OUT_DIR = CODE_DIR / "out"
DDL_DIR = CODE_DIR / "sql" / "ddl"

SOURCE_FILES = {"Fraud_Case_Extract": "DP_Fraud_Case.csv"}

CONTRACT_META = {
    "version": "0.2",
    "owner": "Product Owner - Fraud & Risk Data",
    "refresh": "Daily full rebuild, ready by 07:00 ET",
    "change_policy": "New columns are additive; type changes need 30 days' notice",
    "source_prd": "output/DP_Fraud_Case/PRD_Fraud_Case.md",
    "jira": "SCRUM-25",
    "depends_on": "DP_Member_360 (member_360.member_id); data/reference/account_id_map.csv",
    # Timestamps are US Eastern local time, stored without an offset.
    "timezone": "America/New_York",
}


def _default_sla_days() -> dict[str, int]:
    # Proposed defaults awaiting Fraud Ops sign-off.
    return {"Critical": 30, "High": 45, "Medium": 60, "Low": 90}


@dataclass(frozen=True)
class Settings:
    # Decided: warn. Fully recovered funds can leave a Confirmed Fraud case with $0 loss.
    confirmed_zero_loss_severity: str = "warn"
    sla_days_by_priority: Mapping[str, int] = field(default_factory=_default_sla_days)
    # 0 never blocks; raise once Member 360 receives the full member feed.
    min_member_match_rate: float = 0.0
    # Case type -> allowed queues. None until Fraud Ops supplies the routing matrix.
    allowed_queues_by_case_type: Mapping[str, tuple[str, ...]] | None = None
