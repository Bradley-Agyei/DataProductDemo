# PRD – Account Daily Balance Data Product

| Field | Value |
|---|---|
| Product | DP_Account_Daily_Balance |
| Owner | Product Owner – Finance & Risk Data |
| Status | Draft v0.1 |
| Date | 2026-10-06 |
| Jira | SCRUM-35 (Feature epic) · stories SCRUM-37 to SCRUM-43 (FR-01 to FR-07) |
| Sources | sources/data/raw/ (Account, Transaction, Transaction_Type, Product, Member, Date) + account_id_map |
| Target sample | data/output/product/DP_Account_Daily_Balance.csv (shape only – see Q1) |
| Related products | DP_Payment_Transaction (same transactions), DP_Member_360 (member lookup) |

## 1. Overview

- Finance and risk teams work out daily balances themselves from raw transactions, and they disagree.
- Account Daily Balance is one governed row per account per day: opening, credits, debits, closing, available balance and an overdraft flag.
- Built from the core banking extracts: 10 accounts, 100 transactions, 21–30 Sep 2026.

## 2. Goals, non-goals and success metrics

### Goals

- One trusted daily balance per account, every column typed.
- Balances that always add up: closing = opening + credits − debits, and today's opening = yesterday's closing.
- Overdrafts and negative balances visible the same day.
- Joins cleanly to Payment Transaction and Member 360 on canonical IDs.

### Non-goals (this release)

- Intraday or real-time balances.
- Interest accrual and fee calculation.
- General ledger posting.
- Rebuilding history before go-live.

### Success metrics (proposed targets)

| Metric | Target |
|---|---|
| Accounts × days present | 100% |
| Rows passing balance equation (DQ-05) | 100% |
| Reconciliation to source transactions (DQ-07) | 100%, $0.00 difference |
| Daily refresh ready by 07:00 ET | ≥ 95% of days |

### Counter-metrics (watch so targets aren't gamed)

- Transactions rejected to make DQ pass (should trend to 0).
- Rows published with available_balance NULL.

## 3. Personas

| Persona | Need | Uses Account Daily Balance for |
|---|---|---|
| Finance & reporting analyst | Balances that reconcile | Daily balance reporting, deposit totals by product, month-end tie-out |
| Finance controller | Audit trail | Reconciliation to transactions, exception review |
| Fraud & risk analyst | Spot unusual movement | Overdrafts, sudden balance swings, dormant accounts with activity |
| Data engineering | Clear contract | Build and run the pipeline |

## 4. Scope

### In scope

- Ingest the 6 core banking extracts as-is (raw layer).
- Standardize types; conform account and member IDs.
- Daily credit/debit totals, balance roll-forward over the Date calendar.
- Overdraft flag; available balance once its rule is signed off.
- Exception report, data contract, DDL.

### Out of scope

- Member names, addresses (PII).
- Branch-level reporting (in DP_Payment_Transaction).
- Fixing source balance_after.

## 5. Source data inventory and data types

| Table | Grain | Primary key | Rows (sample) | File |
|---|---|---|---|---|
| Account | One row per account | account_id | 10 | sources/data/raw/Account.csv |
| Transaction | One row per transaction | transaction_id | 100 | sources/data/raw/Transaction.csv |
| Transaction_Type | One row per transaction type | transaction_type_id | 10 | sources/data/raw/Transaction_Type.csv |
| Product | One row per product | product_id | 10 | sources/data/raw/Product.csv |
| Member | One row per member | member_id | 10 | sources/data/raw/Member.csv |
| Date | One row per calendar day | date_key | 10 | sources/data/raw/Date.csv |
| account_id_map | One row per (source system, source account ID) | source_system + source_account_id | 110 | sources/data/reference/account_id_map.csv |

### Type conversion rules

- Currency "$1,225.35 " → DECIMAL(15,2); (x) = negative.
- M/D/YYYY → DATE; YYYYMMDD keys → INT; TRUE/FALSE → BOOLEAN.
- IDs and postal codes stay text and are checked by pattern.

### 5.1 Account (Account.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| account_id | Identifier | VARCHAR(10) | N | PK | A00001 | A + 5 digits. Canonical form A + 7 digits via account_id_map (core_banking rows). |
| member_id | Identifier | VARCHAR(10) | N | FK → Member | M0001 | M + 4 digits. Conform to M + 6 digits (left-pad). |
| product_id | Identifier | VARCHAR(10) | N | FK → Product | P001 | P + 3 digits. |
| branch_id | Identifier | VARCHAR(10) | N | FK → Branch | B001 | B + 3 digits. |
| account_type | Category | VARCHAR(20) | N |  | Checking | Checking, Savings, Money Market, Certificate, Loan, Credit Card. |
| open_date | Date | DATE | N |  | 1/8/2019 | Parse M/D/YYYY. |
| account_status | Category | VARCHAR(12) | N |  | Open | Open, Restricted. Current status only (no history). |
| current_balance | Currency amount | DECIMAL(15,2) | N |  | $500.00  | Strip $, commas and spaces; (x) means negative → DECIMAL(15,2). Equals the balance before the first sample transaction (10 of 10 accounts). |
| currency_code | Code | CHAR(3) | N |  | USD | ISO 4217; USD only in sample. |

### 5.2 Transaction (Transaction.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| transaction_id | Identifier | VARCHAR(12) | N | PK | TXN000001 | TXN + 6 digits; unique. |
| account_id | Identifier | VARCHAR(10) | N | FK → Account | A00001 | A + 5 digits → canonical via account_id_map. |
| member_id | Identifier | VARCHAR(10) | N | FK → Member | M0001 | Matches the account owner on all 100 rows. |
| transaction_type_id | Identifier | VARCHAR(5) | N | FK → Transaction_Type | TT03 |  |
| channel_id | Identifier | VARCHAR(5) | N | FK → Channel | C02 |  |
| branch_id | Identifier | VARCHAR(10) | N | FK → Branch | B001 | Matches the account's branch on all 100 rows. |
| date_key | Date key | INT | N | FK → Date | 20260921 | Date only – no time of day. |
| amount | Currency amount | DECIMAL(15,2) | N |  | $15.00  | Strip $, commas and spaces; (x) means negative → DECIMAL(15,2). Always > 0; direction from debit_credit_indicator. |
| currency_code | Code | CHAR(3) | N |  | USD | USD only. |
| debit_credit_indicator | Category | VARCHAR(6) | N |  | Credit | Credit, Debit. Matches Transaction_Type on all 100 rows. |
| transaction_status | Category | VARCHAR(10) | N |  | Posted | Posted (60), Pending (20), Reversed (20). |
| balance_after | Currency amount | DECIMAL(15,2) | N |  | $515.00  | Strip $, commas and spaces; (x) means negative → DECIMAL(15,2). NOT a running balance: = current_balance ± this amount. 2 negative values. |
| reference_number | Identifier | VARCHAR(16) | N |  | REF202600001 | REF + year + 5 digits; unique. |

### 5.3 Transaction type (Transaction_Type.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| transaction_type_id | Identifier | VARCHAR(5) | N | PK | TT01 | TT + 2 digits. |
| transaction_type_name | Category | VARCHAR(30) | N |  | Withdrawal | Deposit, Withdrawal, ACH Credit, ACH Debit, Card Purchase, Card Refund, Wire In, Wire Out, Fee, Interest. |
| debit_credit_indicator | Category | VARCHAR(6) | N |  | Debit | Expected direction for the type. |
| transaction_category | Category | VARCHAR(20) | N |  | Cash | Funding, Cash, ACH, Card, Wire, Fee, Interest. |

### 5.4 Product (Product.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| product_id | Identifier | VARCHAR(10) | N | PK | P001 | P + 3 digits. |
| product_name | Text | VARCHAR(50) | N |  | Everyday Checking | Display name. No short product code in source. |
| product_category | Category | VARCHAR(20) | N |  | Checking | Checking, Savings, Money Market, Certificate, Loan, Credit Card. |
| currency_code | Code | CHAR(3) | N |  | USD | ISO 4217. |
| monthly_fee | Currency amount | DECIMAL(15,2) | N |  | $5.00  | Strip $, commas and spaces; (x) means negative → DECIMAL(15,2). |
| interest_rate_pct | Percent | DECIMAL(6,3) | N |  | 1.25 | Percent, not a fraction. |
| product_status | Category | VARCHAR(10) | N |  | Active | Active only in sample. |

### 5.5 Member (Member.csv) – member_id and member_status only

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| member_id | Identifier | VARCHAR(10) | N | PK | M0001 | M + 4 digits → M + 6 digits. |
| first_name | PII | VARCHAR(50) | N |  | (PII – not shown) | PII – not published. |
| last_name | PII | VARCHAR(50) | N |  | (PII – not shown) | PII – not published. |
| join_date | Date | DATE | N |  | 1/5/2018 | Parse M/D/YYYY. |
| city | PII | VARCHAR(50) | N |  | (PII – not shown) | PII – not published. |
| state | Code | CHAR(2) | N |  | NC | US state. |
| postal_code | PII | VARCHAR(10) | N |  | (PII – not shown) | Text (keeps leading zeros). PII – not published. |
| member_status | Category | VARCHAR(10) | N |  | Active | Active, Dormant (M0004, M0008 are Dormant). |
| member_segment | Category | VARCHAR(20) | N |  | Retail | Retail, Premium, Student, Small Business. |

### 5.6 Date (Date.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| date_key | Date key | INT | N | PK | 20260921 | YYYYMMDD. |
| full_date | Date | DATE | N |  | 9/21/2026 | Parse M/D/YYYY. Sample covers 21–30 Sep 2026. |
| day_name | Category | VARCHAR(10) | N |  | Monday |  |
| month_name | Category | VARCHAR(10) | N |  | September |  |
| month_number | Integer | SMALLINT | N |  | 9 |  |
| quarter_number | Integer | SMALLINT | N |  | 3 |  |
| year_number | Integer | SMALLINT | N |  | 2026 |  |
| is_weekend | Boolean | BOOLEAN | N |  | FALSE | TRUE/FALSE. |

### 5.7 Reference: account ID mapping (account_id_map.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| source_system | Category | VARCHAR(30) | N | PK | core_banking | System the ID comes from. |
| source_account_id | Identifier | VARCHAR(12) | N | PK | A00001 | Account ID as that system writes it. |
| account_id | Identifier | VARCHAR(10) | N |  | A0000001 | Canonical ^A\d{7}$. |
| in_core_banking | Boolean | BOOLEAN | N |  | TRUE | Canonical ID exists in core banking. |
| mapping_rule | Category | VARCHAR(40) | N |  | pad_to_7_digits | Rule used. |

## 6. Target data product: account_daily_balance

- Grain: one row per account per calendar day.
- Primary key: (account_id, balance_date).
- Refresh: daily; full rebuild of the sample period, idempotent.
- Column order: the 11 sample columns, then derived columns, then audit columns.

| Column | Logical type | Physical type | Null? | Key | Allowed values / format | Description |
|---|---|---|---|---|---|---|
| balance_date | Date | DATE | N | PK | YYYY-MM-DD; a day in the Date dimension | Business day the balance is for. |
| account_id | Identifier | VARCHAR(10) | N | PK | ^A\d{7}$ | Canonical account ID. |
| member_id | Identifier | VARCHAR(10) | N |  | ^M\d{6}$ | Account owner; joins to member_360. |
| product_code | Category | VARCHAR(12) | N |  | CHK_STD, CHK_REW, SAV_STD, SAV_HY, MMA, CD12, PERS_LOAN, AUTO_LOAN, CC_STD, CC_REW | Short product code. |
| account_status | Category | VARCHAR(12) | N |  | Open, Restricted | Account status on the run date. |
| opening_balance | Currency amount | DECIMAL(15,2) | N |  | Any (negative = overdrawn) | Balance at start of day. |
| total_credits | Currency amount | DECIMAL(15,2) | N |  | ≥ 0 | Sum of counted credits that day. |
| total_debits | Currency amount | DECIMAL(15,2) | N |  | ≥ 0 | Sum of counted debits that day. |
| closing_balance | Currency amount | DECIMAL(15,2) | N |  | = opening + credits − debits | Balance at end of day. |
| available_balance | Currency amount | DECIMAL(15,2) | Y |  | ≤ closing_balance | Spendable balance (rule pending). |
| overdraft_flag | Boolean | BOOLEAN | N |  | TRUE / FALSE | closing_balance < 0. |
| transaction_count | Integer | INT | N |  | ≥ 0 | Counted transactions that day. |
| pending_debits | Currency amount | DECIMAL(15,2) | N |  | ≥ 0 | Pending debits that day (not in closing). |
| dp_load_ts | Timestamp | TIMESTAMP | N |  | YYYY-MM-DD HH:MM:SS | Load time. |
| dp_batch_id | Identifier | VARCHAR(36) | N |  | UUID | Pipeline run ID. |

## 7. Source-to-target mapping

| Target column | Source | Rule | Status |
|---|---|---|---|
| balance_date | Date.full_date | Calendar spine: every Date row × every account open on that day. | Mapped (rule) |
| account_id | Account.account_id → account_id_map | Look up core_banking rows; A00001 → A0000001. | Mapped (lookup) |
| member_id | Account.member_id | Left-pad digits to 6: M0001 → M000001. | Mapped (rule) |
| product_code | Account.product_id → product code lookup | No code in source. Proposed lookup P001→CHK_STD … P010→CC_REW (Q6). | GAP – lookup needed |
| account_status | Account.account_status | Copy current status (no history, Q11). | Mapped (direct) |
| opening_balance | Account.current_balance; prior closing_balance | First day = current_balance (Q2); later days = previous day's closing. | Mapped (rule) |
| total_credits | Transaction.amount | Sum where indicator = Credit and status counted (default Posted, Q4). | Mapped (rule) |
| total_debits | Transaction.amount | Sum where indicator = Debit and status counted (default Posted, Q4). | Mapped (rule) |
| closing_balance | derived | opening_balance + total_credits − total_debits. | Mapped (rule) |
| available_balance | derived | Sample = closing − 100.00 on every row; no source for the 100 (Q5). Published NULL until decided. | GAP – rule pending |
| overdraft_flag | derived | closing_balance < 0. | Mapped (rule) |
| transaction_count | Transaction | Count of counted transactions. | Mapped (rule) |
| pending_debits | Transaction.amount | Sum where indicator = Debit and status = Pending. | Mapped (rule) |
| dp_load_ts / dp_batch_id | pipeline | Audit columns. | Mapped (pipeline) |

## 8. Functional requirements

| ID | Requirement | Description |
|---|---|---|
| FR-01 | Ingest core banking extracts | Load Account, Transaction, Transaction_Type, Product, Member and Date unchanged into raw, adding file name, load time and batch ID. Fail fast on a header change. |
| FR-02 | Standardize types and conform IDs | Convert every column to its section-5 type; account IDs to A + 7 digits via account_id_map; member IDs to M + 6 digits. Bad values and duplicate keys go to rejects. |
| FR-03 | Daily credit and debit totals | Per account and day, sum credits and debits for the counted statuses (default Posted); count transactions; total pending debits. |
| FR-04 | Balance roll-forward | Build one row per account per calendar day; opening = previous closing (first day = current_balance); closing = opening + credits − debits; days without activity carry the balance. |
| FR-05 | Available balance and overdraft | Set overdraft_flag (closing < 0); calculate available_balance once the rule is signed off (Settings switch; NULL until then). |
| FR-06 | Account attributes | Add product_code from the product code lookup and the account status; report Dormant members with activity. |
| FR-07 | Publish with DQ gate, exceptions and data contract | Publish table, CSV, data contract and DDL; write the exception report; a blocking DQ failure keeps the previous product. |

### User stories

- As a finance analyst, I want each account's daily opening and closing balance, so that I can report balances without rebuilding them.
- As a finance controller, I want balances to reconcile to transactions, so that I can sign off month-end.
- As a fraud & risk analyst, I want overdrafts and dormant-account activity flagged, so that I can investigate the same day.
- As an analyst, I want canonical account and member IDs, so that I can join to Payment Transaction and Member 360.

## 9. Non-functional requirements

- Daily batch, ready by 07:00 ET; idempotent reruns.
- No PII (no names, addresses or postal codes).
- Lineage via dp_batch_id; run log with rows in / out / rejected.
- A blocking DQ failure keeps the previous published table.
- Undecided rules (Q4, Q5, Q8) are configuration switches, not code changes.

## 10. Data quality rules and acceptance criteria

| Rule | Check | Severity |
|---|---|---|
| DQ-01 | (account_id, balance_date) unique and not null | Critical – block |
| DQ-02 | account_id and member_id match their patterns | Critical – block |
| DQ-03 | All NOT NULL columns populated | Critical – block |
| DQ-04 | account_status and product_code only contain allowed values | Critical – block |
| DQ-05 | closing_balance = opening_balance + total_credits − total_debits | Critical – block |
| DQ-06 | opening_balance = previous day's closing_balance (continuity) | Critical – block |
| DQ-07 | Σ credits and Σ debits per account = Σ counted source transactions (reconciliation) | Critical – block |
| DQ-08 | Every transaction's account exists in Account; every account in account_id_map | High – reject transaction |
| DQ-09 | Transaction debit_credit_indicator = its type's indicator | High – reject transaction |
| DQ-10 | overdraft_flag = (closing_balance < 0) | Critical – block |
| DQ-11 | available_balance ≤ closing_balance (when populated) | Medium – warn |
| DQ-12 | Negative closing balance on Savings, Money Market or Certificate | Medium – warn |
| DQ-13 | Dormant member with activity on the day | Medium – warn |

### Acceptance criteria (release)

- All 15 target columns present with the section-6 types; header starts with the 11 sample columns in order.
- 100 rows from the sample sources (10 accounts × 10 days).
- Every row passes DQ-05 and DQ-06; DQ-07 difference $0.00.
- Hand-checked example: A0000001 on 2026-09-21 opens at $500.00, has $10,213.32 posted credits (10 rows) and closes at $10,713.32.
- Dormant members M000004 and M000008 reported in the exception report.
- All critical DQ rules pass on the sample.

## 11. Open questions and data gaps

Every finding below was checked against the sample files on 2026-10-06.

| # | Finding (verified) | Proposed decision | Status |
|---|---|---|---|
| Q1 | Target sample has 100 accounts (A0000001–A0000100) and 100 members; sources have 10 (A00001–A00010). Sample values don't reconcile (A0000001 opening $363.71 vs source $500.00; status differs for 4 of the first 10). | Treat the sample as shape only; test against the real sources. | Open – PO confirm |
| Q2 | Account.current_balance equals the balance before the first sample transaction (10 of 10 accounts), despite its name. | Use it as the opening balance of the first day. | Open – Finance confirm |
| Q3 | Transaction.balance_after is not a running balance (90 of 100 rows break the chain; each = current_balance ± its own amount). 2 values are negative. | Ignore balance_after; recompute balances. | Open – source owner confirm |
| Q4 | Status mix: 60 Posted, 20 Pending, 20 Reversed. Each account has one status for all its rows (A00004/A00009 Pending only; A00005/A00010 Reversed only). | Count Posted in the ledger; show Pending debits separately; exclude Reversed. Settings switch. | Open – Finance sign-off |
| Q5 | available_balance = closing − 100.00 on all 100 sample rows; no source for the 100. | Publish NULL until the rule is decided (hold, minimum balance or pending debits). | Open – blocks FR-05 |
| Q6 | product_code (CHK_STD…) has no source; codes line up with P001–P010 in order. | Product team supplies a product code reference table. | Open – blocks FR-06 |
| Q7 | Each account trades on one day only (10 account-days). Sample has one row per account. | One row per account per calendar day (10 × 10 = 100), carrying balances forward. | Open – PO confirm |
| Q8 | Loan and Credit Card accounts use the same sign rule as deposits in the sample. | Decide sign convention per product_category (owed vs held). | Open – Finance |
| Q9 | A00003 has Fee debits of $2,150.48 and $2,199.00 that take balance_after negative. | Flag as exceptions; confirm with source owner. | Open |
| Q10 | M0004 and M0008 are Dormant but have 10 transactions each. | Warn (DQ-13); share with Fraud & risk. | Open |
| Q11 | account_status is current only; history isn't kept. | Status on the run date; daily snapshots build history from go-live. | Open |

## 12. Dependencies, risks and milestones

- Depends on sources/data/reference/account_id_map.csv (account ID conformance).
- Depends on a product code reference table (Q6).
- Shares the transaction feed with DP_Payment_Transaction.

| Risk | Mitigation |
|---|---|
| Status rule (Q4) changes balances | Settings switch; DQ-07 reconciles whichever rule is set. |
| Source balance_after used by mistake | Not mapped; documented in Q3. |
| Extract format changes | Header check fails fast (FR-01). |

| Milestone | Content | Est. |
|---|---|---|
| M1 | FR-01, FR-02: ingest + types + ID conformance | Sprint 1 |
| M2 | FR-03, FR-04: daily totals + roll-forward | Sprint 1 |
| M3 | FR-05, FR-06, FR-07: available/overdraft, attributes, publish | Sprint 2 |

## 13. Appendix – sources

- sources/data/raw/Account.csv — 10 rows
- sources/data/raw/Transaction.csv — 100 rows (10 per account, each account on one date)
- sources/data/raw/Transaction_Type.csv, Product.csv, Member.csv, Date.csv — 10 rows each
- sources/data/reference/account_id_map.csv — 110 rows
- data/output/product/DP_Account_Daily_Balance.csv — 100-row target sample (shape only)
- Profile (verified): sample closing = opening + credits − debits on 100/100 rows; closing − available = 100.00 on 100/100; overdraft_flag FALSE on all.
