"""Product contracts: DP_Member_360 and its companion tables."""
from src.dp_framework.contract import PENDING, Column as C, Table

from .sources import MEMBER_SEGMENTS

AGE_BANDS = ("18-24", "25-34", "35-44", "45-54", "55-64", "65+")
KYC_STATUSES = ("Verified", "Review Required")
RISK_RATINGS = ("Low", "Medium", "High")
RELATIONSHIP_STATUSES = ("Active", "Dormant", "Restricted")

MEMBER_360 = Table("member_360", (
    C("member_id", "VARCHAR(10)", key="PK", pattern=r"M\d{6}", description="Unique member ID, conformed format."),
    C("member_since_date", "DATE", description="Date the member joined."),
    C("member_segment", "VARCHAR(20)", allowed=MEMBER_SEGMENTS, description="Business segment."),
    C("age_band", "VARCHAR(5)", nullable=True, allowed=AGE_BANDS, status=PENDING,
      description="Age group. Exact age/DOB never published. Needs DOB feed."),
    C("home_state", "CHAR(2)", pattern=r"[A-Z]{2}", description="Member's home state (USPS)."),
    C("digital_enrolled_flag", "BOOLEAN", status=PENDING,
      description="Enrolled in online or mobile banking. Needs enrollment feed."),
    C("kyc_status", "VARCHAR(20)", allowed=KYC_STATUSES, status=PENDING,
      description="Know-Your-Customer status. Needs KYC/CIP feed."),
    C("risk_rating", "VARCHAR(10)", allowed=RISK_RATINGS, status=PENDING,
      description="Member risk rating. Needs risk/AML feed."),
    C("relationship_status", "VARCHAR(15)", allowed=RELATIONSHIP_STATUSES, description="Overall relationship status."),
    C("last_profile_update_ts", "TIMESTAMP", status=PENDING,
      description="Last profile change. Needs audit/CDC feed."),
    C("dp_load_ts", "TIMESTAMP", description="When the row was loaded."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID, for lineage."),
), grain="One row per member", description="Governed, typed single view of each member.")

MEMBER_ID_XREF = Table("member_id_xref", (
    C("source_member_id", "VARCHAR(10)", key="PK", description="Member ID as it appears in the source."),
    C("member_id", "VARCHAR(10)", key="UNIQUE", pattern=r"M\d{6}", description="Conformed member ID."),
    C("source_system", "VARCHAR(30)", description="Source system name."),
    C("dp_load_ts", "TIMESTAMP", description="When the row was loaded."),
), grain="One row per source member ID")

DQ_EXCEPTIONS = Table("dq_exceptions", (
    C("exception_type", "VARCHAR(40)", description="Exception category."),
    C("member_id", "VARCHAR(10)", nullable=True, description="Conformed member ID."),
    C("account_id", "VARCHAR(10)", nullable=True, description="Account involved."),
    C("transaction_id", "VARCHAR(12)", nullable=True, description="Transaction involved."),
    C("detail", "VARCHAR(200)", description="Plain-English explanation."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
), grain="One row per exception found")
