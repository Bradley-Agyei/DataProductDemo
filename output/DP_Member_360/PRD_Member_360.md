# PRD – Member 360 Data Product

| Field | Value |
|---|---|
| Product | DP_Member_360 |
| Owner | Product Owner – Member Data |
| Status | Draft v0.1 |
| Date | 2026-10-04 |
| Jira | SCRUM-17 (Feature epic) · stories SCRUM-18 to SCRUM-24 (FR-01 to FR-07) · account ID mapping SCRUM-32 |
| Sources | data/raw/*.csv (8 files) |
| Target sample | data/product/DP_Member_360.csv |

## 1. Overview

- Member data is spread across 8 tables (members, accounts, products, branches, channels, dates, transactions, transaction types).
- No single, trusted view of a member exists — each team rebuilds it and gets different answers.
- Member 360 is one row per member with the attributes most teams need: segment, tenure, home state, digital enrollment, KYC, risk and relationship status.

## 2. Goals, non-goals and success metrics

### Goals

- One governed, documented, typed table: one row per member.
- Every column has a defined data type, allowed values and a source or rule.
- Refreshed daily and checked by automated data quality (DQ) rules.
- Safe to share: no direct PII (names, exact DOB, postal code).

### Non-goals (this release)

- Transaction-level analytics or a balance/ledger product.
- Real-time / streaming updates.
- Building the KYC, risk or digital-enrollment systems themselves (we consume them).
- Dashboards (consumers build their own on top of the product).

### Success metrics (proposed targets)

| Metric | Target |
|---|---|
| Source members present in product | 100% |
| Duplicate member_id | 0 |
| Rows passing all critical DQ rules | ≥ 99.5% |
| Daily refresh ready by 07:00 ET | ≥ 95% of days |
| Columns with documented type + rule | 100% |
| Consuming teams after 1 quarter | ≥ 3 |

## 3. Personas

| Persona | Need | Uses Member 360 for |
|---|---|---|
| Business / branch leaders | Know who their members are | Segment and state mix, dormant members to re-engage |
| Data analysts / BI | Clean, joinable data | Join key for any member-level report |
| Risk & compliance | Spot exceptions fast | KYC review queue, high-risk and restricted members |
| Marketing | Right audience | Digital-enrolled vs not, segment targeting |
| Data engineering | Clear contract | Build, test and run the pipeline to spec |

## 4. Scope

### In scope

- Ingest the 8 source CSVs as-is (raw layer).
- Standardize data types per section 5.
- Conform member_id to M + 6 digits, with crosswalk.
- Build DP_Member_360 (10 columns, section 6).
- DQ rules, rejects table, and run log.
- Data contract + catalog entry; role-based access.

### Out of scope

- Changes to source systems.
- Account- or transaction-level products (future).
- Historic snapshots / SCD2 (future; v1 is current-state).

## 5. Source data inventory and data types

| Table | Grain | Primary key | Rows (sample) | File |
|---|---|---|---|---|
| Account | One row per account | account_id | 10 | data/raw/Account.csv |
| Branch | One row per branch | branch_id | 10 | data/raw/Branch.csv |
| Channel | One row per channel | channel_id | 10 | data/raw/Channel.csv |
| Date | One row per calendar day | date_key | 10 | data/raw/Date.csv |
| Member | One row per member | member_id | 10 | data/raw/Member.csv |
| Product | One row per product | product_id | 10 | data/raw/Product.csv |
| Transaction | One row per transaction | transaction_id | 100 | data/raw/Transaction.csv |
| Transaction_Type | One row per transaction type | transaction_type_id | 10 | data/raw/Transaction_Type.csv |

### Relationships

- Transaction → Account, Member, Transaction_Type, Channel, Branch, Date (many-to-one).
- Account → Member, Product, Branch (many-to-one).
- All foreign keys resolve in the sample (100% referential integrity).

### Type conversion rules (apply to all tables)

- Currency text like "$1,225.35 " → strip $, commas and spaces → DECIMAL.
- Parentheses mean negative: ($199.78) → -199.78.
- Dates in M/D/YYYY → DATE (ISO 8601).
- TRUE/FALSE text → BOOLEAN.
- Postal codes and IDs stay as text (never numeric — keeps leading zeros).
- Category values are trimmed and validated against the allowed list.

### 5.1 Account

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| account_id | Identifier | VARCHAR(10) | N | PK | A00001 | Unique account ID. |
| member_id | Identifier | VARCHAR(10) | N | FK → Member | M0001 | Owning member. |
| product_id | Identifier | CHAR(4) | N | FK → Product | P001 | Product the account is opened on. |
| branch_id | Identifier | CHAR(4) | N | FK → Branch | B001 | Home branch of the account. |
| account_type | Category | VARCHAR(20) | N |  | Checking | Checking, Savings, Money Market, Certificate, Loan, Credit Card. |
| open_date | Date | DATE | N |  | 1/8/2019 | Parse M/D/YYYY → ISO date. |
| account_status | Category | VARCHAR(15) | N |  | Open | Open, Restricted. |
| current_balance | Currency amount | DECIMAL(15,2) | N |  | "$1,225.35 " | Strip $, commas, trailing space; (x) = negative. |
| currency_code | Code (ISO 4217) | CHAR(3) | N |  | USD | Always USD today. |

### 5.2 Branch

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| branch_id | Identifier | CHAR(4) | N | PK | B001 | Unique branch ID. |
| branch_name | Text | VARCHAR(50) | N |  | Uptown | Branch display name. |
| city | Text | VARCHAR(50) | N |  | Charlotte | Branch city. |
| state | Code (USPS) | CHAR(2) | N |  | NC | 2-letter state code. |
| postal_code | Code | CHAR(5) | N |  | 28210 | Keep as text (leading zeros). |
| time_zone | Category | VARCHAR(20) | N |  | Eastern | Eastern, Central. |
| branch_status | Category | VARCHAR(10) | N |  | Open | Open. |

### 5.3 Channel

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| channel_id | Identifier | CHAR(3) | N | PK | C01 | Unique channel ID. |
| channel_name | Text | VARCHAR(30) | N |  | Mobile App | Channel display name. |
| channel_group | Category | VARCHAR(20) | N |  | Digital | Assisted, Self-Service, Digital, External, System. |

### 5.4 Date

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| date_key | Integer key | INT | N | PK | 20260921 | YYYYMMDD smart key. |
| full_date | Date | DATE | N |  | 9/21/2026 | Parse M/D/YYYY → ISO date. |
| day_name | Text | VARCHAR(9) | N |  | Monday | Day of week. |
| month_name | Text | VARCHAR(9) | N |  | September | Month name. |
| month_number | Integer | SMALLINT | N |  | 9 | 1–12. |
| quarter_number | Integer | SMALLINT | N |  | 3 | 1–4. |
| year_number | Integer | SMALLINT | N |  | 2026 | 4-digit year. |
| is_weekend | Boolean | BOOLEAN | N |  | FALSE | TRUE/FALSE → boolean. |

### 5.5 Member

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| member_id | Identifier | VARCHAR(10) | N | PK | M0001 | Source format M + 4 digits. |
| first_name | Text (PII) | VARCHAR(50) | N |  | (PII – not shown) | PII — not published in product. |
| last_name | Text (PII) | VARCHAR(50) | N |  | (PII – not shown) | PII — not published in product. |
| join_date | Date | DATE | N |  | 1/5/2018 | Parse M/D/YYYY → ISO date. |
| city | Text | VARCHAR(50) | N |  | Charlotte | Member city. |
| state | Code (USPS) | CHAR(2) | N |  | NC | 2-letter state code. |
| postal_code | Code (PII) | CHAR(5) | N |  | (PII – not shown) | Keep as text; quasi-identifier. |
| member_status | Category | VARCHAR(15) | N |  | Active | Active, Dormant. |
| member_segment | Category | VARCHAR(20) | N |  | Retail | Retail, Premium, Student, Small Business. |

### 5.6 Product

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| product_id | Identifier | CHAR(4) | N | PK | P001 | Unique product ID. |
| product_name | Text | VARCHAR(50) | N |  | Everyday Checking | Product display name. |
| product_category | Category | VARCHAR(20) | N |  | Checking | Matches account_type values. |
| currency_code | Code (ISO 4217) | CHAR(3) | N |  | USD | Always USD today. |
| monthly_fee | Currency amount | DECIMAL(10,2) | N |  | "$5.00 " | Strip $ and trailing space. |
| interest_rate_pct | Percentage | DECIMAL(5,2) | N |  | 3.75 | Percent value (3.75 = 3.75%). |
| product_status | Category | VARCHAR(10) | N |  | Active | Active. |

### 5.7 Transaction

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| transaction_id | Identifier | VARCHAR(12) | N | PK | TXN000001 | Unique transaction ID. |
| account_id | Identifier | VARCHAR(10) | N | FK → Account | A00001 | Account posted to. |
| member_id | Identifier | VARCHAR(10) | N | FK → Member | M0001 | Member (denormalized from account). |
| transaction_type_id | Identifier | CHAR(4) | N | FK → Transaction_Type | TT03 | Transaction type. |
| channel_id | Identifier | CHAR(3) | N | FK → Channel | C02 | Channel used. |
| branch_id | Identifier | CHAR(4) | N | FK → Branch | B001 | Branch attributed. |
| date_key | Integer key | INT | N | FK → Date | 20260921 | Transaction date (YYYYMMDD). |
| amount | Currency amount | DECIMAL(15,2) | N |  | "$1,082.74 " | Always positive; sign comes from debit_credit_indicator. |
| currency_code | Code (ISO 4217) | CHAR(3) | N |  | USD | Always USD today. |
| debit_credit_indicator | Category | VARCHAR(6) | N |  | Credit | Debit, Credit; must match Transaction_Type. |
| transaction_status | Category | VARCHAR(10) | N |  | Posted | Posted, Pending, Reversed. |
| balance_after | Currency amount | DECIMAL(15,2) | N |  | ($199.78) | (x) = negative. NOT a running balance (see gaps). |
| reference_number | Identifier | VARCHAR(20) | N | Unique | REF202600001 | External reference. |

### 5.8 Transaction_Type

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| transaction_type_id | Identifier | CHAR(4) | N | PK | TT01 | Unique type ID. |
| transaction_type_name | Text | VARCHAR(30) | N |  | Deposit | Type display name. |
| debit_credit_indicator | Category | VARCHAR(6) | N |  | Credit | Debit, Credit. |
| transaction_category | Category | VARCHAR(20) | N |  | Funding | Funding, Cash, ACH, Card, Wire, Fee, Interest. |

### 5.9 Reference: account ID mapping table (data/reference/account_id_map.csv)

- Shared reference data, built and validated by tools/build_account_id_map.py and tools/validate_account_id_map.py.
- Canonical account ID = A + 7 digits; any source width is zero-padded (A0001, A00001 → A0000001).
- Grain: one row per (source_system, source_account_id); one-to-one within a system, many-to-one across systems.
- Member 360 uses it for DQ-11: every core banking account must be mapped.

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| source_system | Category | VARCHAR(30) | N | PK | core_banking | System the ID comes from (core_banking, fraud_case_mgmt). |
| source_account_id | Identifier | VARCHAR(12) | N | PK | A00001 | Account ID as that system writes it. |
| account_id | Identifier | VARCHAR(10) | N |  | A0000001 | Canonical ^A\d{7}$ (zero-padded). |
| in_core_banking | Boolean | BOOLEAN | N |  | TRUE | Canonical ID exists in core banking. |
| mapping_rule | Category | VARCHAR(40) | N |  | pad_to_7_digits | Rule used to derive account_id. |

## 6. Target data product: DP_Member_360

- Grain: one row per member.
- Primary key: member_id.
- Location (sample): data/product/DP_Member_360.csv.
- Refresh: daily, full rebuild (current state).

| Column | Logical type | Physical type | Null? | Key | Allowed values / format | Description |
|---|---|---|---|---|---|---|
| member_id | Identifier | VARCHAR(10) | N | PK | M + 6 digits (M000001) | Unique member ID, conformed format. |
| member_since_date | Date | DATE | N |  | YYYY-MM-DD | Date the member joined. |
| member_segment | Category | VARCHAR(20) | N |  | Retail, Premium, Student, Small Business | Business segment. |
| age_band | Category | VARCHAR(5) | Y |  | 18-24, 25-34, 35-44, 45-54, 55-64, 65+ | Age group. Exact age/DOB never published. |
| home_state | Code (USPS) | CHAR(2) | N |  | NC, SC, GA, FL, VA, MD, TN | Member's home state. |
| digital_enrolled_flag | Boolean | BOOLEAN | N |  | TRUE / FALSE | Member is enrolled in online or mobile banking. |
| kyc_status | Category | VARCHAR(20) | N |  | Verified, Review Required | Know-Your-Customer verification status. |
| risk_rating | Category | VARCHAR(10) | N |  | Low, Medium, High | Member risk rating. |
| relationship_status | Category | VARCHAR(15) | N |  | Active, Dormant, Restricted | Overall relationship status. |
| last_profile_update_ts | Timestamp | TIMESTAMP | N |  | YYYY-MM-DD HH:MM:SS (ET) | Last time the member profile changed. |

### Recommended audit columns (not in sample)

| Column | Logical type | Physical type | Null? | Key | Description |
|---|---|---|---|---|---|
| dp_load_ts | Timestamp | TIMESTAMP | N |  | When the row was loaded. |
| dp_batch_id | Identifier | VARCHAR(36) | N |  | Pipeline run ID (UUID) for lineage. |

## 7. Source-to-target mapping

| Target column | Source | Rule | Status |
|---|---|---|---|
| member_id | Member.member_id | 'M' + LPAD(numeric part, 6, '0'); e.g. M0001 → M000001. Keep crosswalk table. | Mapped (transform) |
| member_since_date | Member.join_date | Parse M/D/YYYY → DATE. | Mapped (transform) |
| member_segment | Member.member_segment | Direct copy; validate against allowed list. | Mapped (direct) |
| age_band | — none — | Needs date_of_birth from core/CIF. Band = age at run date, bucketed. | GAP – new source |
| home_state | Member.state | Direct copy; validate USPS code. | Mapped (direct) |
| digital_enrolled_flag | — none (proxy: Transaction.channel_id) — | Preferred: digital-banking enrollment table. Proxy: TRUE if any txn via C03/C04 in last 90 days. | GAP – decision needed |
| kyc_status | — none — | Needs KYC / CIP system feed. | GAP – new source |
| risk_rating | — none — | Needs risk / AML scoring system feed. | GAP – new source |
| relationship_status | Member.member_status + Account.account_status | Restricted if ANY account is Restricted; else member_status (Active/Dormant). | Mapped (rule – confirm) |
| last_profile_update_ts | — none — | Needs audit / CDC timestamp on member profile. Interim: pipeline load timestamp. | GAP – new source |

- 5 of 10 columns can be built from today's sources.
- 5 columns need a new feed or a decision (see section 11).

## 8. Functional requirements

| ID | Requirement | Description |
|---|---|---|
| FR-01 | Ingest sources | Load the 8 CSVs into a raw layer unchanged, adding file name and load timestamp. |
| FR-02 | Standardize data types | Convert every column to the physical type in section 5; failed rows go to a rejects table with a reason. |
| FR-03 | Conform member ID | Convert member_id to M + 6 digits and keep a source→target crosswalk. |
| FR-04 | Build Member 360 core | Populate member_id, member_since_date, member_segment, home_state, relationship_status per section 7. |
| FR-05 | Integrate new attribute feeds | Add age_band, digital_enrolled_flag, kyc_status, risk_rating, last_profile_update_ts once source feeds are agreed. |
| FR-06 | Data quality and exceptions | Run DQ rules in section 10; block publish on critical failures; report exceptions. |
| FR-07 | Publish and govern | Publish the table with data contract, catalog entry, column descriptions and role-based access. |

### User stories

- As an analyst, I want one row per member with typed columns, so that I can join and report without cleaning data.
- As a compliance officer, I want kyc_status and risk_rating on each member, so that I can prioritize reviews.
- As a marketer, I want digital_enrolled_flag and segment, so that I can target digital adoption campaigns.
- As a branch leader, I want relationship_status by home_state, so that I can re-engage dormant members.
- As a data engineer, I want a documented contract and DQ rules, so that I can build and test with confidence.

## 9. Non-functional requirements

- Freshness: daily batch, ready by 07:00 ET.
- Reruns: idempotent — rerunning the same day gives the same result.
- Privacy: no names, DOB or postal code in the product; age only as a band.
- Access: role-based; kyc_status and risk_rating restricted to approved roles.
- Lineage: every row traceable to source files via dp_batch_id.
- Auditability: run log with row counts in/out/rejected per table.
- Performance: full rebuild completes in < 15 minutes at 1M members.

## 10. Data quality rules and acceptance criteria

| Rule | Check | Severity |
|---|---|---|
| DQ-01 | member_id is unique and not null | Critical – block |
| DQ-02 | member_id matches ^M\d{6}$ | Critical – block |
| DQ-03 | All NOT NULL columns populated | Critical – block |
| DQ-04 | Category columns only contain allowed values (section 6) | Critical – block |
| DQ-05 | member_since_date ≤ run date | High – reject row |
| DQ-06 | home_state is a valid USPS code | High – reject row |
| DQ-07 | Product row count = distinct source members (reconciliation) | Critical – block |
| DQ-08 | last_profile_update_ts ≤ load time | Medium – warn |
| DQ-09 | Source FKs resolve (Account→Member, Transaction→Account, etc.) | High – reject row |
| DQ-10 | Transaction.debit_credit_indicator matches Transaction_Type | Medium – warn |
| DQ-11 | Every Account.account_id is in the account ID mapping reference table (core_banking) | High – reject row |

### Acceptance criteria (release)

- All 10 target columns present with the exact physical types in section 6.
- All critical DQ rules pass on the sample sources.
- Mapping rules in section 7 produce expected values for all 10 source members.
- Data contract and catalog entry published; access roles tested.

## 11. Open questions and data gaps

| # | Finding (from sample data) | Impact | Decision needed / owner |
|---|---|---|---|
| Q1 | Member IDs differ: sources use M0001–M0010 (10 members); target sample has M000001–M000100 (100 members). | 90 target rows have no source. | Confirm ID format and full member source – PO / Data Eng |
| Q2 | Overlapping IDs don't match: e.g. M0001 joined 1/5/2018, Retail, NC vs M000001 joined 2/2/2015, Premium, VA. | Target sample looks illustrative, not derived. | Confirm target is a shape example only – PO |
| Q3 | No source for age_band, kyc_status, risk_rating, last_profile_update_ts. | 5 of 10 columns blocked. | Identify systems of record – PO / Compliance |
| Q4 | digital_enrolled_flag: enrollment feed vs. channel-usage proxy (C03/C04). | Definition changes counts. | Choose definition – PO / Digital |
| Q5 | 'Restricted' exists in target but not in Member.member_status (Active/Dormant only). | Needs account-level rule. | Approve rule in section 7 – PO / Compliance |
| Q6 | Dormant members M0004 and M0008 own Restricted accounts that still have 10 transactions each (Pending withdrawals; Posted ACH debits). | Possible compliance exception. | Should these surface as an exception flag? – Compliance |
| Q7 | Negative balance_after on Savings account A00003: TXN000023 ($199.78) and TXN000073 ($248.30). | Overdraft on a savings product. | Valid or data error? – Ops |
| Q8 | balance_after = account current_balance ± that one transaction, not a running balance. | Can't be used for balance history. | Confirm meaning – Data Eng |
| Q9 | Sample target correlates perfectly: Small Business always Restricted + Review Required; Student always Dormant. | Not realistic test data. | Provide realistic test data – Data Eng |
| Q10 | Loan / credit card balances are positive like deposits. | Sign convention unclear. | Confirm liability sign convention – Finance |
| Q11 | Account IDs differ by system: core banking A00001 vs fraud case mgmt A0000001. | Cross-product account joins failed. | DECIDED (SCRUM-32): canonical A + 7 digits via data/reference/account_id_map.csv; enforced by DQ-11 |

## 12. Dependencies, risks and milestones

### Dependencies

- Feeds for DOB, KYC, risk rating, digital enrollment and profile audit timestamps.
- Agreed member ID standard across systems.
- Data platform with scheduling, DQ framework and role-based access.

### Risks

| Risk | Mitigation |
|---|---|
| New feeds delayed | Release core (5 columns) first; add others as nullable until available. |
| ID mismatch across systems | Crosswalk table + DQ-07 reconciliation. |
| PII leakage | Only banded/derived attributes; access review before publish. |

### Milestones (proposed)

| Milestone | Content | Est. |
|---|---|---|
| M1 | FR-01, FR-02: ingest + typed staging | Sprint 1 |
| M2 | FR-03, FR-04, FR-06: core product + DQ | Sprint 2 |
| M3 | FR-05: new attribute feeds | Sprint 3–4 (depends on Q3/Q4) |
| M4 | FR-07: publish + govern | Sprint 4 |

## 13. Appendix – sources

- data/raw/Account.csv — 10 rows, columns: account_id, member_id, product_id, branch_id, account_type, open_date, account_status, current_balance, currency_code
- data/raw/Branch.csv — 10 rows, columns: branch_id, branch_name, city, state, postal_code, time_zone, branch_status
- data/raw/Channel.csv — 10 rows, columns: channel_id, channel_name, channel_group
- data/raw/Date.csv — 10 rows, columns: date_key, full_date, day_name, month_name, month_number, quarter_number, year_number, is_weekend
- data/raw/Member.csv — 10 rows, columns: member_id, first_name, last_name, join_date, city, state, postal_code, member_status, member_segment
- data/raw/Product.csv — 10 rows, columns: product_id, product_name, product_category, currency_code, monthly_fee, interest_rate_pct, product_status
- data/raw/Transaction.csv — 100 rows, columns: transaction_id, account_id, member_id, transaction_type_id, channel_id, branch_id, date_key, amount, currency_code, debit_credit_indicator, transaction_status, balance_after, reference_number
- data/raw/Transaction_Type.csv — 10 rows, columns: transaction_type_id, transaction_type_name, debit_credit_indicator, transaction_category

- data/product/DP_Member_360.csv — 100 rows, columns: member_id, member_since_date, member_segment, age_band, home_state, digital_enrolled_flag, kyc_status, risk_rating, relationship_status, last_profile_update_ts
- data/reference/account_id_map.csv — 110 rows, columns: source_system, source_account_id, account_id, in_core_banking, mapping_rule
