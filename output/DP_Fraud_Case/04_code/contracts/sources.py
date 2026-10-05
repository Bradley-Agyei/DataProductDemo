"""Source contract: the case-management extract, one Column per CSV column."""
from src.dp_framework.contract import Column as C, Table

CASE_TYPES = ("Account Takeover", "ACH Fraud", "Wire Fraud", "Identity Review", "Card Fraud")
ALERT_SOURCES = ("ML Model", "Member Report", "Operations Review", "Rules Engine")
CASE_STATUSES = ("Open", "Investigating", "Escalated", "Closed")
PRIORITIES = ("Low", "Medium", "High", "Critical")
QUEUES = ("Deposit Ops", "Digital Fraud", "Enhanced Review", "Card Ops")
RESOLUTIONS = ("Confirmed Fraud", "False Positive")

CASE_ID_PATTERN = r"FC\d{7}"
MEMBER_ID_PATTERN = r"M\d{6}"
ACCOUNT_ID_PATTERN = r"A\d{7}"

FRAUD_CASE_EXTRACT = Table("Fraud_Case_Extract", (
    C("case_id", "VARCHAR(10)", key="PK", pattern=CASE_ID_PATTERN, description="Fraud case ID."),
    C("member_id", "VARCHAR(10)", pattern=MEMBER_ID_PATTERN, description="Member on the case."),
    C("primary_account_id", "VARCHAR(10)", pattern=ACCOUNT_ID_PATTERN,
      description="Primary account; format differs from the banking sources."),
    C("case_open_ts", "TIMESTAMP", description="When the case opened (ET, America/New_York)."),
    C("case_type", "VARCHAR(30)", allowed=CASE_TYPES, description="Fraud type."),
    C("alert_source", "VARCHAR(30)", allowed=ALERT_SOURCES, description="What raised the alert."),
    C("case_status", "VARCHAR(15)", allowed=CASE_STATUSES, description="Case lifecycle status."),
    C("priority", "VARCHAR(10)", allowed=PRIORITIES, description="Case priority."),
    C("suspected_loss_amount", "DECIMAL(15,2)", description="Loss suspected at intake."),
    C("confirmed_loss_amount", "DECIMAL(15,2)", description="Loss confirmed at close; 0 until confirmed."),
    C("assigned_queue", "VARCHAR(30)", allowed=QUEUES, description="Work queue."),
    C("resolution_code", "VARCHAR(20)", nullable=True, allowed=RESOLUTIONS, description="Set only when Closed."),
    C("case_close_ts", "TIMESTAMP", nullable=True, description="When the case closed (ET); set only when Closed."),
), grain="One row per fraud case")

SOURCES = {FRAUD_CASE_EXTRACT.name: FRAUD_CASE_EXTRACT}
