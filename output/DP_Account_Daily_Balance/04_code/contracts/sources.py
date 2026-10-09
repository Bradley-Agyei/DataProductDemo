"""Non-PII source contracts used to standardize the core banking extracts."""
from src.dp_framework.contract import Column as C, Table

CURRENCIES = ("USD",)
ACCOUNT_TYPES = ("Checking", "Savings", "Money Market", "Certificate", "Loan", "Credit Card")
ACCOUNT_STATUSES = ("Open", "Restricted")
MEMBER_STATUSES = ("Active", "Dormant")
MEMBER_SEGMENTS = ("Retail", "Premium", "Student", "Small Business")
DEBIT_CREDIT = ("Debit", "Credit")
TRANSACTION_STATUSES = ("Posted", "Pending", "Reversed")

ACCOUNT = Table("Account", (
    C("account_id", "VARCHAR(10)", key="PK", pattern=r"A\d{7}"),
    C("member_id", "VARCHAR(10)", pattern=r"M\d{6}"),
    C("product_id", "CHAR(4)"),
    C("branch_id", "CHAR(4)"),
    C("account_type", "VARCHAR(20)", allowed=ACCOUNT_TYPES),
    C("open_date", "DATE"),
    C("account_status", "VARCHAR(15)", allowed=ACCOUNT_STATUSES),
    C("current_balance", "DECIMAL(15,2)"),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES),
), grain="One row per account")

TRANSACTION = Table("Transaction", (
    C("transaction_id", "VARCHAR(12)", key="PK"),
    C("account_id", "VARCHAR(10)", pattern=r"A\d{7}"),
    C("member_id", "VARCHAR(10)", pattern=r"M\d{6}"),
    C("transaction_type_id", "CHAR(4)"),
    C("channel_id", "CHAR(3)"),
    C("branch_id", "CHAR(4)"),
    C("date_key", "INT", pattern=r"\d{8}"),
    C("amount", "DECIMAL(15,2)"),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES),
    C("debit_credit_indicator", "VARCHAR(6)", allowed=DEBIT_CREDIT),
    C("transaction_status", "VARCHAR(10)", allowed=TRANSACTION_STATUSES),
    C("balance_after", "DECIMAL(15,2)"),
    C("reference_number", "VARCHAR(20)", key="UNIQUE"),
), grain="One row per transaction")

TRANSACTION_TYPE = Table("Transaction_Type", (
    C("transaction_type_id", "CHAR(4)", key="PK"),
    C("transaction_type_name", "VARCHAR(30)"),
    C("debit_credit_indicator", "VARCHAR(6)", allowed=DEBIT_CREDIT),
    C("transaction_category", "VARCHAR(20)"),
), grain="One row per transaction type")

PRODUCT = Table("Product", (
    C("product_id", "CHAR(4)", key="PK"),
    C("product_name", "VARCHAR(50)"),
    C("product_category", "VARCHAR(20)", allowed=ACCOUNT_TYPES),
    C("currency_code", "CHAR(3)", allowed=CURRENCIES),
    C("monthly_fee", "DECIMAL(10,2)"),
    C("interest_rate_pct", "DECIMAL(5,2)"),
    C("product_status", "VARCHAR(10)"),
), grain="One row per product")

MEMBER = Table("Member", (
    C("member_id", "VARCHAR(10)", key="PK", pattern=r"M\d{6}"),
    C("join_date", "DATE"),
    C("state", "CHAR(2)"),
    C("member_status", "VARCHAR(15)", allowed=MEMBER_STATUSES),
    C("member_segment", "VARCHAR(20)", allowed=MEMBER_SEGMENTS),
), grain="One row per member")

DATE = Table("Date", (
    C("date_key", "INT", key="PK", pattern=r"\d{8}"),
    C("full_date", "DATE"),
    C("day_name", "VARCHAR(9)"),
    C("month_name", "VARCHAR(9)"),
    C("month_number", "SMALLINT"),
    C("quarter_number", "SMALLINT"),
    C("year_number", "SMALLINT"),
    C("is_weekend", "BOOLEAN"),
), grain="One row per calendar day")

SOURCES = {
    table.name: table
    for table in (ACCOUNT, TRANSACTION, TRANSACTION_TYPE, PRODUCT, MEMBER, DATE)
}
