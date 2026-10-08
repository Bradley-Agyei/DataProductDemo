"""Source table contracts for DP_Payment_Transaction: one entry per column of the 7 source CSVs.

Physical types and keys follow PRD_Payment_Transaction.md §5 (pinned by tests/test_source_contract.py).
"""
from src.dp_framework.contract import Column as C, Table

CURRENCIES = ("USD",)
ACCOUNT_TYPES = ("Checking", "Savings", "Money Market", "Certificate", "Loan", "Credit Card")
ACCOUNT_STATUSES = ("Open", "Restricted")
MEMBER_STATUSES = ("Active", "Dormant")
MEMBER_SEGMENTS = ("Retail", "Premium", "Student", "Small Business")
DEBIT_CREDIT = ("Debit", "Credit")
TRANSACTION_STATUSES = ("Posted", "Pending", "Reversed")

ACCOUNT = Table("Account", (
    C("account_id", "VARCHAR(10)", key="PK", description="Unique account ID."),
    C("member_id", "VARCHAR(10)", key="FK:Member.member_id", description="Owning member."),
    C("product_id", "VARCHAR(10)", key="FK:Product.product_id", description="Product the account is opened on."),
    C("branch_id", "VARCHAR(10)", key="FK:Branch.branch_id", description="Home branch of the account."),
    C("account_type", "VARCHAR(20)", allowed=ACCOUNT_TYPES, description="Account type."),
    C("open_date", "DATE", description="Date the account was opened."),
    C("account_status", "VARCHAR(12)", allowed=ACCOUNT_STATUSES, description="Account status."),
    C("current_balance", "DECIMAL(15,2)", description="Current balance."),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES, description="ISO 4217 currency."),
), grain="One row per account")

BRANCH = Table("Branch", (
    C("branch_id", "VARCHAR(10)", key="PK", description="Unique branch ID."),
    C("branch_name", "VARCHAR(50)", description="Branch display name."),
    C("city", "VARCHAR(50)", description="Branch city; masked in raw (PRD §5.5: matches member PII)."),
    C("state", "CHAR(2)", description="USPS state code."),
    C("postal_code", "VARCHAR(10)", description="ZIP code, kept as text; masked in raw (PRD §5.5)."),
    C("time_zone", "VARCHAR(10)", description="Branch time zone."),
    C("branch_status", "VARCHAR(10)", description="Branch status."),
), grain="One row per branch")

CHANNEL = Table("Channel", (
    C("channel_id", "VARCHAR(5)", key="PK", description="Unique channel ID."),
    C("channel_name", "VARCHAR(30)", description="Channel display name."),
    C("channel_group", "VARCHAR(20)", description="Assisted, Self-Service, Digital, External, System."),
), grain="One row per channel")

DATE = Table("Date", (
    C("date_key", "INT", key="PK", description="YYYYMMDD smart key."),
    C("full_date", "DATE", description="Calendar date."),
    C("day_name", "VARCHAR(10)", description="Day of week."),
    C("month_name", "VARCHAR(10)", description="Month name."),
    C("month_number", "SMALLINT", description="1-12."),
    C("quarter_number", "SMALLINT", description="1-4."),
    C("year_number", "SMALLINT", description="4-digit year."),
    C("is_weekend", "BOOLEAN", description="Saturday or Sunday."),
), grain="One row per calendar day")

MEMBER = Table("Member", (
    C("member_id", "VARCHAR(10)", key="PK", pattern=r"M\d+", description="Source member ID (M + digits)."),
    C("first_name", "VARCHAR(50)", description="PII: never published."),
    C("last_name", "VARCHAR(50)", description="PII: never published."),
    C("join_date", "DATE", description="Date the member joined."),
    C("city", "VARCHAR(50)", description="PII (PRD §5.7): masked in raw."),
    C("state", "CHAR(2)", description="USPS state code."),
    C("postal_code", "VARCHAR(10)", description="PII: ZIP code, kept as text; masked in raw."),
    C("member_status", "VARCHAR(10)", allowed=MEMBER_STATUSES, description="Member status."),
    C("member_segment", "VARCHAR(20)", allowed=MEMBER_SEGMENTS, description="Business segment."),
), grain="One row per member")


TRANSACTION = Table("Transaction", (
    C("transaction_id", "VARCHAR(12)", key="PK", description="Unique transaction ID."),
    C("account_id", "VARCHAR(10)", key="FK:Account.account_id", description="Account posted to."),
    C("member_id", "VARCHAR(10)", key="FK:Member.member_id", description="Member (denormalized from account)."),
    C("transaction_type_id", "VARCHAR(5)", key="FK:Transaction_Type.transaction_type_id",
      description="Transaction type."),
    C("channel_id", "VARCHAR(5)", key="FK:Channel.channel_id", description="Channel used."),
    C("branch_id", "VARCHAR(10)", key="FK:Branch.branch_id", description="Branch attributed."),
    C("date_key", "INT", key="FK:Date.date_key", description="Transaction date (YYYYMMDD)."),
    C("amount", "DECIMAL(15,2)", description="Always positive; sign comes from debit_credit_indicator."),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES, description="ISO 4217 currency."),
    C("debit_credit_indicator", "VARCHAR(6)", allowed=DEBIT_CREDIT, description="Must match the transaction type."),
    C("transaction_status", "VARCHAR(10)", allowed=TRANSACTION_STATUSES, description="Transaction status."),
    C("balance_after", "DECIMAL(15,2)", description="Account balance +/- this transaction (not a running balance)."),
    C("reference_number", "VARCHAR(16)", description="External reference; duplicates are a DQ-12 warning, not a key."),
), grain="One row per transaction")

TRANSACTION_TYPE = Table("Transaction_Type", (
    C("transaction_type_id", "VARCHAR(5)", key="PK", description="Unique type ID."),
    C("transaction_type_name", "VARCHAR(30)", description="Type display name."),
    C("debit_credit_indicator", "VARCHAR(6)", allowed=DEBIT_CREDIT, description="Debit or Credit."),
    C("transaction_category", "VARCHAR(20)", description="Funding, Cash, ACH, Card, Wire, Fee, Interest."),
), grain="One row per transaction type")

# Order follows the story: the transaction extract, then its reference tables.
SOURCES = {t.name: t for t in (TRANSACTION, TRANSACTION_TYPE, CHANNEL, DATE, BRANCH, ACCOUNT, MEMBER)}
