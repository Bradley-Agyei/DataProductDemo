# PRD – Payment Transaction Data Product

| Field | Value |
|---|---|
| Product | DP_Payment_Transaction |
| Owner | Product Owner – Finance & Risk Data |
| Status | Draft v0.1 |
| Date | 2026-10-06 |
| Jira | SCRUM-36 (Feature epic) · stories SCRUM-44, SCRUM-50, SCRUM-45 to SCRUM-49 (FR-01 to FR-07) |
| Sources | sources/data/raw/ (Transaction, Transaction_Type, Channel, Date, Branch, Account, Member) + account_id_map |
| Target sample | data/output/product/DP_Payment_Transaction.csv (shape only – see Q1) |
| Related products | DP_Account_Daily_Balance (same transactions), DP_Member_360, DP_Fraud_Case |

## 1. Overview

- Transactions are spread across a fact file and five code tables; every team joins them its own way.
- Payment Transaction is one governed, readable row per transaction: type, channel, amount, direction, status and canonical IDs.
- Built from the core banking extracts: 100 transactions on 10 accounts, 21–30 Sep 2026.

## 2. Goals, non-goals and success metrics

### Goals

- One trusted transaction table, every column typed and decoded.
- Catch broken transactions (wrong direction, unknown keys, member ≠ owner) before reporting.
- Give Fraud & risk the signals they need: signed amounts, dormant activity, member link.
- Same IDs as Account Daily Balance, Member 360 and Fraud Case.

### Non-goals (this release)

- Fraud scoring or alerting.
- Real-time feeds.
- Inventing merchant, country or time values that aren't in the source.

### Success metrics (proposed targets)

| Metric | Target |
|---|---|
| Source transactions published or rejected with a reason | 100% |
| Duplicate transaction_id | 0 |
| Rows passing integrity checks | ≥ 99.5% |
| Daily refresh ready by 07:00 ET | ≥ 95% of days |
| Member match rate to member_360 | Tracked; 100% on sample |

### Counter-metrics

- Rows rejected (should trend to 0, not be hidden).
- Share of rows with pending gap columns.

## 3. Personas

| Persona | Need | Uses Payment Transaction for |
|---|---|---|
| Finance & reporting analyst | Volumes and values that tie out | Volumes by type and channel, tie-out to daily balances |
| Fraud & risk analyst | Clean, decoded activity | Dormant-account activity, unusual type/channel pairs, link to fraud cases |
| Fraud operations | Case context | Transactions behind a fraud case |
| Data engineering | Clear contract | Build and run the pipeline |

## 4. Scope

### In scope

- Ingest the transaction extract and its reference tables (raw layer).
- Standardize types; conform transaction, account and member IDs.
- Decode type, channel and date; integrity checks; fraud and risk signals.
- Gap columns published as NULL and marked pending.
- Exception report, data contract, DDL.

### Out of scope

- Member names and addresses (PII).
- Balances (in DP_Account_Daily_Balance).
- Linking reversals to originals.

## 5. Source data inventory and data types

| Table | Grain | Primary key | Rows (sample) | File |
|---|---|---|---|---|
| Transaction | One row per transaction | transaction_id | 100 | sources/data/raw/Transaction.csv |
| Transaction_Type | One row per transaction type | transaction_type_id | 10 | sources/data/raw/Transaction_Type.csv |
| Channel | One row per channel | channel_id | 10 | sources/data/raw/Channel.csv |
| Date | One row per calendar day | date_key | 10 | sources/data/raw/Date.csv |
| Branch | One row per branch | branch_id | 10 | sources/data/raw/Branch.csv |
| Account | One row per account | account_id | 10 | sources/data/raw/Account.csv |
| Member | One row per member | member_id | 10 | sources/data/raw/Member.csv |
| account_id_map | One row per (source system, source account ID) | source_system + source_account_id | 110 | sources/data/reference/account_id_map.csv |

### Type conversion rules

- Currency "$1,082.74 " → DECIMAL(15,2); (x) = negative.
- M/D/YYYY → DATE; YYYYMMDD keys → INT; TRUE/FALSE → BOOLEAN.
- IDs and postal codes stay text and are checked by pattern.

### 5.1 Transaction (Transaction.csv)

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

### 5.2 Transaction type (Transaction_Type.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| transaction_type_id | Identifier | VARCHAR(5) | N | PK | TT01 | TT + 2 digits. |
| transaction_type_name | Category | VARCHAR(30) | N |  | Withdrawal | Deposit, Withdrawal, ACH Credit, ACH Debit, Card Purchase, Card Refund, Wire In, Wire Out, Fee, Interest. |
| debit_credit_indicator | Category | VARCHAR(6) | N |  | Debit | Expected direction for the type. |
| transaction_category | Category | VARCHAR(20) | N |  | Cash | Funding, Cash, ACH, Card, Wire, Fee, Interest. |

### 5.3 Channel (Channel.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| channel_id | Identifier | VARCHAR(5) | N | PK | C01 | C + 2 digits. |
| channel_name | Category | VARCHAR(30) | N |  | Online Banking | Branch, ATM, Online Banking, Mobile App, Call Center, ACH Network, Card Network, Wire Desk, Batch Processing, API. |
| channel_group | Category | VARCHAR(20) | N |  | Digital | Assisted, Self-Service, Digital, External, System. |

### 5.4 Date (Date.csv)

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

### 5.5 Branch (Branch.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| branch_id | Identifier | VARCHAR(10) | N | PK | B001 | B + 3 digits. |
| branch_name | Text | VARCHAR(50) | N |  | Uptown |  |
| city | Text | VARCHAR(50) | N |  | (not shown – matches member PII) |  |
| state | Code | CHAR(2) | N |  | NC | NC, GA, VA, TN, SC, FL, MD. |
| postal_code | Code | VARCHAR(10) | N |  | (not shown – matches member PII) | Text. |
| time_zone | Category | VARCHAR(10) | N |  | Eastern | Eastern, Central. |
| branch_status | Category | VARCHAR(10) | N |  | Open | Open only in sample. |

### 5.6 Account (Account.csv) – ownership check

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

### 5.7 Member (Member.csv) – member_id and member_status only

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

### 5.8 Reference: account ID mapping (account_id_map.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| source_system | Category | VARCHAR(30) | N | PK | core_banking | System the ID comes from. |
| source_account_id | Identifier | VARCHAR(12) | N | PK | A00001 | Account ID as that system writes it. |
| account_id | Identifier | VARCHAR(10) | N |  | A0000001 | Canonical ^A\d{7}$. |
| in_core_banking | Boolean | BOOLEAN | N |  | TRUE | Canonical ID exists in core banking. |
| mapping_rule | Category | VARCHAR(40) | N |  | pad_to_7_digits | Rule used. |

## 6. Target data product: payment_transaction

- Grain: one row per transaction.
- Primary key: transaction_id.
- Refresh: daily full rebuild, idempotent.
- Column order: the 12 sample columns, then derived columns, then audit columns.

| Column | Logical type | Physical type | Null? | Key | Allowed values / format | Description |
|---|---|---|---|---|---|---|
| transaction_id | Identifier | VARCHAR(12) | N | PK | ^TXN\d{9}$ | Transaction ID. |
| transaction_ts | Timestamp | TIMESTAMP | Y |  | YYYY-MM-DD HH:MM:SS (ET) | When the transaction happened. Time not in source (Q2). |
| account_id | Identifier | VARCHAR(10) | N |  | ^A\d{7}$ | Canonical account ID. |
| member_id | Identifier | VARCHAR(10) | N |  | ^M\d{6}$ | Account owner; joins to member_360. |
| transaction_type | Category | VARCHAR(30) | N |  | Deposit, ATM Withdrawal, ACH Credit, ACH Debit, Card Purchase, Card Refund, Wire In, Wire Out (+ Fee, Interest – Q5) | Transaction type name. |
| channel | Category | VARCHAR(30) | N |  | Branch, ATM, Online, Mobile, ACH Network, Card Network, API (+ Call Center, Wire Desk, Batch Processing – Q6) | Channel the transaction came through. |
| merchant_category | Category | VARCHAR(30) | Y |  | Dining, Financial, Fuel, Grocery, Retail, Travel, Utilities, Not Applicable | Merchant category. No source (Q3). |
| amount | Currency amount | DECIMAL(15,2) | N |  | > 0 | Transaction amount (unsigned). |
| debit_credit_indicator | Category | VARCHAR(6) | N |  | Credit, Debit | Direction of money. |
| transaction_status | Category | VARCHAR(10) | N |  | Posted, Pending, Reversed | Processing status. |
| country_code | Code | CHAR(2) | Y |  | ISO 3166-1 alpha-2 | Country of the transaction. No source (Q4). |
| reference_number | Identifier | VARCHAR(16) | N |  | ^REF\d{9,10}$ | External reference. |
| transaction_date | Date | DATE | N |  | YYYY-MM-DD | Business date of the transaction. |
| signed_amount | Currency amount | DECIMAL(15,2) | N |  | Credit +, Debit − | Amount with direction applied. |
| transaction_category | Category | VARCHAR(20) | N |  | Funding, Cash, ACH, Card, Wire, Fee, Interest | Type group. |
| channel_group | Category | VARCHAR(20) | N |  | Assisted, Self-Service, Digital, External, System | Channel group. |
| branch_id | Identifier | VARCHAR(10) | N |  | ^B\d{3}$ | Branch of the account. |
| member_found_flag | Boolean | BOOLEAN | N |  | TRUE / FALSE | Member exists in member_360. |
| dp_load_ts | Timestamp | TIMESTAMP | N |  | YYYY-MM-DD HH:MM:SS | Load time. |
| dp_batch_id | Identifier | VARCHAR(36) | N |  | UUID | Pipeline run ID. |

## 7. Source-to-target mapping

| Target column | Source | Rule | Status |
|---|---|---|---|
| transaction_id | Transaction.transaction_id | Left-pad digits to 9: TXN000001 → TXN000000001 (Q7). | Mapped (rule) |
| transaction_ts | Transaction.date_key → Date.full_date | Date known; time of day has no source. Published NULL until a time feed exists (Q2). | GAP – time missing |
| account_id | Transaction.account_id → account_id_map | core_banking rows; A00001 → A0000001. | Mapped (lookup) |
| member_id | Transaction.member_id | Left-pad digits to 6: M0001 → M000001. | Mapped (rule) |
| transaction_type | Transaction_Type.transaction_type_name | Look up by transaction_type_id; rename Withdrawal → ATM Withdrawal (Q5). | Mapped (lookup) |
| channel | Channel.channel_name | Look up by channel_id; rename Online Banking → Online, Mobile App → Mobile (Q6). | Mapped (lookup) |
| merchant_category | — | No source. NULL, marked pending (Q3). | GAP – no source |
| amount | Transaction.amount | Currency text → DECIMAL(15,2). | Mapped (direct) |
| debit_credit_indicator | Transaction.debit_credit_indicator | Copy; must match the type's indicator (DQ-07). | Mapped (direct) |
| transaction_status | Transaction.transaction_status | Copy. | Mapped (direct) |
| country_code | — | No source (all branches are US). NULL, marked pending (Q4). | GAP – no source |
| reference_number | Transaction.reference_number | Copy as-is; format change still open (Q7). | Mapped (direct) |
| transaction_date | Transaction.date_key → Date.full_date | Date lookup. | Mapped (lookup) |
| signed_amount | amount, debit_credit_indicator | +amount for Credit, −amount for Debit. | Mapped (rule) |
| transaction_category | Transaction_Type.transaction_category | Look up by transaction_type_id. | Mapped (lookup) |
| channel_group | Channel.channel_group | Look up by channel_id. | Mapped (lookup) |
| branch_id | Transaction.branch_id | Copy. | Mapped (direct) |
| member_found_flag | member_360.member_id | member_id IN member_360; unmatched rows kept and reported. | Mapped (lookup) |
| dp_load_ts / dp_batch_id | pipeline | Audit columns. | Mapped (pipeline) |

## 8. Functional requirements

| ID | Requirement | Description |
|---|---|---|
| FR-01 | Ingest transaction extracts | Load Transaction, Transaction_Type, Channel, Date, Branch, Account and Member unchanged into raw, adding file name, load time and batch ID. Fail fast on a header change. |
| FR-02 | Standardize types and conform IDs | Convert every column to its section-5 type; transaction IDs to TXN + 9 digits, account IDs via account_id_map, member IDs to M + 6 digits. Bad values and duplicate IDs go to rejects. |
| FR-03 | Enrich with reference data | Add type, category, channel, channel group and business date from the lookups, applying the agreed name mapping. |
| FR-04 | Transaction integrity checks | Reject transactions with unknown keys, a direction that contradicts their type, a non-positive amount, or a member who doesn't own the account. |
| FR-05 | Fraud and risk signals | Add signed_amount and member_found_flag; report Dormant-member activity and duplicate reference numbers. |
| FR-06 | Columns without a source | Publish transaction_ts, merchant_category and country_code as NULL, marked pending in the data contract, until a source is agreed. |
| FR-07 | Publish with DQ gate, exceptions and data contract | Publish table, CSV, data contract (timezone ET) and DDL; write the exception report; a blocking DQ failure keeps the previous product. |

### User stories

- As a finance analyst, I want decoded transaction types and channels, so that I can report volumes without joining code tables.
- As a fraud & risk analyst, I want dormant-member activity flagged, so that I can review it the same day.
- As a fraud ops analyst, I want canonical account and member IDs, so that I can link transactions to fraud cases.
- As a data consumer, I want gap columns clearly marked pending, so that I don't trust made-up values.

## 9. Non-functional requirements

- Daily batch, ready by 07:00 ET; idempotent reruns.
- No PII (no names, addresses or postal codes).
- Lineage via dp_batch_id; run log with rows in / out / rejected.
- A blocking DQ failure keeps the previous published table.
- Name mappings (Q5, Q6) and the type/channel matrix are configuration, not code.

## 10. Data quality rules and acceptance criteria

| Rule | Check | Severity |
|---|---|---|
| DQ-01 | transaction_id unique and not null | Critical – block |
| DQ-02 | transaction_id, account_id, member_id, reference_number match their patterns | Critical – block |
| DQ-03 | All NOT NULL columns populated (pending gap columns skipped) | Critical – block |
| DQ-04 | Category columns only contain allowed values | Critical – block |
| DQ-05 | Published + rejected rows = source rows (reconciliation) | Critical – block |
| DQ-06 | account, type, channel, branch and date keys all resolve | High – reject row |
| DQ-07 | debit_credit_indicator = the type's indicator | High – reject row |
| DQ-08 | amount > 0 | High – reject row |
| DQ-09 | Transaction member = account owner | High – reject row |
| DQ-10 | transaction_date not after the run date | High – reject row |
| DQ-11 | Activity on a Dormant member | Medium – warn |
| DQ-12 | reference_number unique | Medium – warn |
| DQ-13 | member_id found in member_360 | Medium – warn (row kept, flagged) |
| DQ-14 | Type allowed for channel (only when a matrix is configured) | Medium – warn |

### Acceptance criteria (release)

- All 20 target columns present with the section-6 types; header starts with the 12 sample columns in order.
- 100 rows published from the sample sources; 0 rejected.
- TXN000001 publishes as TXN000000001, A0000001, M000001, ACH Credit, ATM, $15.00, Credit, Posted, 2026-09-21, signed +15.00.
- 20 Dormant-member transactions (M000004, M000008) in the exception report.
- transaction_ts, merchant_category and country_code NULL and marked pending in the data contract.
- All critical DQ rules pass on the sample.

## 11. Open questions and data gaps

Every finding below was checked against the sample files on 2026-10-06.

| # | Finding (verified) | Proposed decision | Status |
|---|---|---|---|
| Q1 | Target sample has 100 accounts and members; sources have 10. Sample rows don't line up with source rows (TXN000000001 = ACH Credit / Online / $93.27; source TXN000001 = ACH Credit / ATM / $15.00). | Treat the sample as shape only; test against the real sources. | Open – PO confirm |
| Q2 | transaction_ts needs a time, but the source has only date_key. Branches span Eastern and Central time. | Publish transaction_date now; transaction_ts NULL until the source adds a time (ET). | Open – blocks full FR-06 |
| Q3 | merchant_category has no source (sample values: Dining, Fuel, Grocery…, Not Applicable for ATM). | NULL + pending; card network MCC feed needed. | Open – source owner |
| Q4 | country_code has no source; all 10 branches are in US states, but the sample has CA and GB. | NULL + pending; don't default to US. | Open – source owner |
| Q5 | Source type 'Withdrawal' vs sample 'ATM Withdrawal'. Fee and Interest (20 source rows) aren't in the sample. | Rename Withdrawal → ATM Withdrawal; keep Fee and Interest (they move money) unless Finance excludes them. | Open – Finance / Fraud |
| Q6 | Channel names differ: Online Banking → Online, Mobile App → Mobile. Call Center, Wire Desk, Batch Processing (30 source rows) aren't in the sample. | Rename the two; keep the other three as allowed values. | Open – PO confirm |
| Q7 | ID widths: TXN + 6 digits in source vs TXN + 9 in sample; REF202600001 (12 chars) vs REF2026100001 (13 chars). | Pad transaction_id to 9 digits; copy reference_number unchanged (external ID). | Open – source owner |
| Q8 | Odd type/channel pairs in source (ACH Credit via ATM, Fee via ACH Network, Card Refund via Batch). | No hard rule; optional DQ-14 warning once Fraud & risk supplies a matrix. | Open |
| Q9 | Pending and Reversed rows (40 of 100) have no link to the original or reversing transaction. | Publish with status; link later if the source adds it. | Open |
| Q10 | M0004 and M0008 are Dormant but have 10 transactions each. | Warn (DQ-11); report to Fraud & risk. | Open |
| Q11 | A00003 has Fee debits of $2,150.48 and $2,199.00. | Exception for review; confirm with source owner. | Open |

## 12. Dependencies, risks and milestones

- Depends on sources/data/reference/account_id_map.csv.
- Depends on DP_Member_360's published member_360 for member_found_flag.
- Needs source feeds for time of day, merchant category and country (Q2–Q4).

| Risk | Mitigation |
|---|---|
| Gap columns stay NULL for long | Marked pending in the contract; tracked as counter-metric. |
| Name mapping disagreements | Configurable mapping; PO sign-off on Q5/Q6. |
| Extract format changes | Header check fails fast (FR-01). |

| Milestone | Content | Est. |
|---|---|---|
| M1 | FR-01, FR-02: ingest + types + ID conformance | Sprint 1 |
| M2 | FR-03, FR-04: enrichment + integrity checks | Sprint 1 |
| M3 | FR-05, FR-06, FR-07: risk signals, gap columns, publish | Sprint 2 |

## 13. Appendix – sources

- sources/data/raw/Transaction.csv — 100 rows (Posted 60, Pending 20, Reversed 20)
- sources/data/raw/Transaction_Type.csv, Channel.csv, Date.csv, Branch.csv, Account.csv, Member.csv — 10 rows each
- sources/data/reference/account_id_map.csv — 110 rows
- data/output/product/DP_Payment_Transaction.csv — 100-row target sample (shape only)
- Profile (verified): 0 duplicate IDs, 0 orphan keys, 0 direction mismatches, member = account owner on 100/100.
