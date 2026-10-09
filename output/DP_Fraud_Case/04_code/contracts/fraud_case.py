"""Product contracts: fraud_case, its status history and its exception report."""
from src.dp_framework.contract import Column as C, Table

from .sources import FRAUD_CASE_EXTRACT

DERIVED = (
    C("is_closed", "BOOLEAN", description="case_status = Closed."),
    C("days_to_close", "DECIMAL(7,2)", nullable=True, description="Days from open to close; closed cases only."),
    C("case_age_days", "INT", nullable=True, description="Whole days from open to run date; open cases only."),
    C("loss_confirmation_ratio", "DECIMAL(5,4)", nullable=True,
      description="confirmed / suspected loss; closed cases only."),
    C("member_found_flag", "BOOLEAN", description="member_id exists in member_360."),
    C("account_found_flag", "BOOLEAN",
      description="primary_account_id maps to a core banking account in the account ID mapping reference table."),
    C("sla_days", "INT", description="SLA in days for the case priority."),
    C("sla_breached_flag", "BOOLEAN",
      description="Closed: days_to_close > sla_days. Open: case_age_days > sla_days."),
    C("dp_load_ts", "TIMESTAMP", description="When the row was loaded."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID, for lineage."),
)

FRAUD_CASE = Table("fraud_case", FRAUD_CASE_EXTRACT.columns + DERIVED, grain="One row per fraud case",
                   description="Governed, typed fraud cases with lifecycle checks, loss metrics and SLA tracking.")

FRAUD_CASE_STATUS_SNAPSHOT = Table("fraud_case_status_snapshot", (
    C("snapshot_date", "DATE", key="PK", description="Run date the snapshot was taken."),
    C("case_id", "VARCHAR(10)", key="PK", description="Fraud case ID."),
    C("case_status", "VARCHAR(15)", description="Status on the snapshot date."),
    C("priority", "VARCHAR(10)", description="Priority on the snapshot date."),
    C("assigned_queue", "VARCHAR(30)", description="Queue on the snapshot date."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
), grain="One row per case per run date")

DQ_EXCEPTIONS = Table("dq_exceptions", (
    C("exception_type", "VARCHAR(40)", description="Exception category."),
    C("case_id", "VARCHAR(10)", description="Case involved."),
    C("member_id", "VARCHAR(10)", nullable=True, description="Member on the case."),
    C("detail", "VARCHAR(200)", description="Plain-English explanation."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
), grain="One row per exception found")
