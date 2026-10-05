"""Source table contracts: one entry per column of the 8 source CSVs."""
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
    C("product_id", "CHAR(4)", key="FK:Product.product_id", description="Product the account is opened on."),
    C("branch_id", "CHAR(4)", key="FK:Branch.branch_id", description="Home branch of the account."),
    C("account_type", "VARCHAR(20)", allowed=ACCOUNT_TYPES, description="Account type."),
    C("open_date", "DATE", description="Date the account was opened."),
    C("account_status", "VARCHAR(15)", allowed=ACCOUNT_STATUSES, description="Account status."),
    C("current_balance", "DECIMAL(15,2)", description="Current balance."),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES, description="ISO 4217 currency."),
), grain="One row per account")

BRANCH = Table("Branch", (
    C("branch_id", "CHAR(4)", key="PK", description="Unique branch ID."),
    C("branch_name", "VARCHAR(50)", description="Branch display name."),
    C("city", "VARCHAR(50)", description="Branch city."),
    C("state", "CHAR(2)", description="USPS state code."),
    C("postal_code", "CHAR(5)", description="ZIP code, kept as text."),
    C("time_zone", "VARCHAR(20)", description="Branch time zone."),
    C("branch_status", "VARCHAR(10)", description="Branch status."),
), grain="One row per branch")

CHANNEL = Table("Channel", (
    C("channel_id", "CHAR(3)", key="PK", description="Unique channel ID."),
    C("channel_name", "VARCHAR(30)", description="Channel display name."),
    C("channel_group", "VARCHAR(20)", description="Assisted, Self-Service, Digital, External, System."),
), grain="One row per channel")

DATE = Table("Date", (
    C("date_key", "INT", key="PK", description="YYYYMMDD smart key."),
    C("full_date", "DATE", description="Calendar date."),
    C("day_name", "VARCHAR(9)", description="Day of week."),
    C("month_name", "VARCHAR(9)", description="Month name."),
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
    C("city", "VARCHAR(50)", description="Member city."),
    C("state", "CHAR(2)", description="USPS state code."),
    C("postal_code", "CHAR(5)", description="ZIP code (quasi-identifier), kept as text."),
    C("member_status", "VARCHAR(15)", allowed=MEMBER_STATUSES, description="Member status."),
    C("member_segment", "VARCHAR(20)", allowed=MEMBER_SEGMENTS, description="Business segment."),
), grain="One row per member")

PRODUCT = Table("Product", (
    C("product_id", "CHAR(4)", key="PK", description="Unique product ID."),
    C("product_name", "VARCHAR(50)", description="Product display name."),
    C("product_category", "VARCHAR(20)", allowed=ACCOUNT_TYPES, description="Matches account_type."),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES, description="ISO 4217 currency."),
    C("monthly_fee", "DECIMAL(10,2)", description="Monthly fee."),
    C("interest_rate_pct", "DECIMAL(5,2)", description="Percent value (3.75 = 3.75%)."),
    C("product_status", "VARCHAR(10)", description="Product status."),
), grain="One row per product")

TRANSACTION = Table("Transaction", (
    C("transaction_id", "VARCHAR(12)", key="PK", description="Unique transaction ID."),
    C("account_id", "VARCHAR(10)", key="FK:Account.account_id", description="Account posted to."),
    C("member_id", "VARCHAR(10)", key="FK:Member.member_id", description="Member (denormalized from account)."),
    C("transaction_type_id", "CHAR(4)", key="FK:Transaction_Type.transaction_type_id", description="Transaction type."),
    C("channel_id", "CHAR(3)", key="FK:Channel.channel_id", description="Channel used."),
    C("branch_id", "CHAR(4)", key="FK:Branch.branch_id", description="Branch attributed."),
    C("date_key", "INT", key="FK:Date.date_key", description="Transaction date (YYYYMMDD)."),
    C("amount", "DECIMAL(15,2)", description="Always positive; sign comes from debit_credit_indicator."),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES, description="ISO 4217 currency."),
    C("debit_credit_indicator", "VARCHAR(6)", allowed=DEBIT_CREDIT, description="Must match the transaction type."),
    C("transaction_status", "VARCHAR(10)", allowed=TRANSACTION_STATUSES, description="Transaction status."),
    C("balance_after", "DECIMAL(15,2)", description="Account balance +/- this transaction (not a running balance)."),
    C("reference_number", "VARCHAR(20)", key="UNIQUE", description="External reference."),
), grain="One row per transaction")

TRANSACTION_TYPE = Table("Transaction_Type", (
    C("transaction_type_id", "CHAR(4)", key="PK", description="Unique type ID."),
    C("transaction_type_name", "VARCHAR(30)", description="Type display name."),
    C("debit_credit_indicator", "VARCHAR(6)", allowed=DEBIT_CREDIT, description="Debit or Credit."),
    C("transaction_category", "VARCHAR(20)", description="Funding, Cash, ACH, Card, Wire, Fee, Interest."),
), grain="One row per transaction type")

SOURCES = {t.name: t for t in (ACCOUNT, BRANCH, CHANNEL, DATE, MEMBER, PRODUCT, TRANSACTION, TRANSACTION_TYPE)}
