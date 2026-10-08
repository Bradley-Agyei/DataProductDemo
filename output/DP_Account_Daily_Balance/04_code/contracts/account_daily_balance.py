"""Product contract: account_daily_balance (target schema from Jira epic SCRUM-35, PRD §6).

The PRD and data dictionary are not in the repo yet; types, rules and order follow
the epic's target schema table. Column order is publish order: the first 11
columns are the sample columns.
"""
from src.dp_framework.contract import PENDING, Column as C, Table

ACCOUNT_STATUSES = ("Open", "Restricted")
PRODUCT_CODES = ("CHK_STD", "CHK_REW", "SAV_STD", "SAV_HY", "MMA", "CD12",
                 "PERS_LOAN", "AUTO_LOAN", "CC_STD", "CC_REW")

ACCOUNT_DAILY_BALANCE = Table("account_daily_balance", (
    C("balance_date", "DATE", key="PK", description="Calendar day (Date calendar x accounts)."),
    C("account_id", "VARCHAR(10)", key="PK", pattern=r"A\d{7}",
      description="Canonical account ID via account_id_map."),
    C("member_id", "VARCHAR(10)", pattern=r"M\d{6}", description="Canonical member ID (M + 6 digits)."),
    C("product_code", "VARCHAR(12)", allowed=PRODUCT_CODES, status=PENDING,
      description="Product code from the product code reference table (Q6, FR-06); NULL until supplied."),
    C("account_status", "VARCHAR(12)", allowed=ACCOUNT_STATUSES, description="Current account status."),
    C("opening_balance", "DECIMAL(15,2)", description="Prior day's closing; day 1 = Account.current_balance."),
    C("total_credits", "DECIMAL(15,2)", description="Sum of counted credits."),
    C("total_debits", "DECIMAL(15,2)", description="Sum of counted debits."),
    C("closing_balance", "DECIMAL(15,2)", description="opening + credits - debits."),
    C("available_balance", "DECIMAL(15,2)", nullable=True, status=PENDING,
      description="Spendable balance; rule pending (Q5, FR-05), NULL until signed off."),
    C("overdraft_flag", "BOOLEAN", description="closing_balance < 0."),
    C("transaction_count", "INT", description="Counted transactions."),
    C("pending_debits", "DECIMAL(15,2)", description="Sum of Pending debits."),
    C("dp_load_ts", "TIMESTAMP", description="When the run loaded the data."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
), grain="One row per account per calendar day",
   description="Governed daily balance per account: opening, credits, debits, closing, overdraft.")

DQ_EXCEPTIONS = Table("dq_exceptions", (
    C("exception_type", "VARCHAR(10)", allowed=("REJECT", "WARN"), description="Rejected row or warning."),
    C("rule_id", "VARCHAR(10)", description="DQ rule that raised it."),
    C("table_name", "VARCHAR(50)", description="Table the row came from."),
    C("row_key", "VARCHAR(100)", description="Primary key value(s) of the row."),
    C("detail", "VARCHAR(200)", description="Plain-English explanation; PII values are masked with *."),
    C("dp_batch_id", "VARCHAR(36)", description="Pipeline run ID."),
), grain="One row per rejected row or warning")
