# PRD – Fraud Case Data Product

| Field | Value |
|---|---|
| Product | DP_Fraud_Case |
| Owner | Product Owner – Fraud & Risk Data |
| Status | Draft v0.1 |
| Date | 2026-10-05 |
| Jira | SCRUM-25 (Feature epic) · stories SCRUM-26 to SCRUM-32 (FR-01 to FR-07) |
| Source | data/raw/DP_Fraud_Case.csv (case-management extract) |
| Target sample | data/product/DP_Fraud_Case.csv |
| Related product | DP_Member_360 (member lookup) |

## 1. Overview

- Fraud cases live in the case-management system. Analysts export them by hand and each team calculates losses and case aging its own way.
- Fraud Case is one governed, typed row per case, with lifecycle checks, loss metrics and a link to Member 360.
- Source: the case-management extract (100 cases opened 1 Aug – 3 Sep 2026).

## 2. Goals, non-goals and success metrics

### Goals

- One trusted table of fraud cases, with every column typed.
- Catch broken case lifecycles (e.g. Closed with no close date) before anyone reports on them.
- Standard metrics: days to close, open-case age, loss confirmation ratio.
- Link each case to Member 360 without dropping cases.

### Non-goals (this release)

- Fraud detection or scoring (alerts come from upstream).
- Changing case routing or queue assignment.
- Real-time feeds; case history / status changes over time (SCD2).

### Success metrics (proposed targets)

| Metric | Target |
|---|---|
| Source cases present in product | 100% |
| Duplicate case_id | 0 |
| Cases passing lifecycle checks | ≥ 99.5% |
| Daily refresh ready by 07:00 ET | ≥ 95% of days |
| Member match rate to member_360 | Tracked; target ≥ 99% once Member 360 covers all members |

## 3. Personas

| Persona | Need | Uses Fraud Case for |
|---|---|---|
| Fraud operations lead | Know what's open and aging | Queue workload, critical cases past SLA |
| Risk & finance | Accurate loss numbers | Suspected vs confirmed loss, confirmation ratio |
| Compliance | Audit trail | Lifecycle completeness, resolution codes |
| Data analysts | Clean, joinable data | Join to Member 360 on member_id |
| Data engineering | Clear contract | Build and run the pipeline |

## 4. Scope

### In scope

- Ingest the case extract as-is (raw layer).
- Standardize types per section 5.
- Lifecycle and loss DQ rules.
- Member link to member_360 and account link via the account ID mapping reference table (keep and flag unmatched).
- Derived metrics and SLA by priority (section 6).
- Daily case status snapshot (history from go-live).
- Exception report, data contract, DDL.

### Out of scope

- Rebuilding status history before go-live.
- Enforcing queue routing (optional DQ-13 check only).
- Case notes, attachments, investigator names (PII).

## 5. Source data inventory and data types

| Table | Grain | Primary key | Rows (sample) | File |
|---|---|---|---|---|
| Fraud case extract | One row per fraud case | case_id | 100 | data/raw/DP_Fraud_Case.csv |

### Type conversion rules

- Currency "$1,060.33 " → DECIMAL(15,2).
- Timestamps M/D/YYYY H:MM → TIMESTAMP.
- Blank resolution_code / case_close_ts → NULL.
- IDs are text and validated by pattern.

### 5.1 Fraud case extract (DP_Fraud_Case.csv)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| case_id | Identifier | VARCHAR(10) | N | PK | FC0000001 | FC + 7 digits; unique. |
| member_id | Identifier | VARCHAR(10) | N | → member_360 | M000001 | M + 6 digits (already conformed format). |
| primary_account_id | Identifier | VARCHAR(10) | N |  | A0000001 | A + 7 digits. Does NOT match banking source (A00001). |
| case_open_ts | Timestamp | TIMESTAMP | N |  | 8/1/2026 8:00 | Parse M/D/YYYY H:MM. US Eastern (America/New_York), no offset. |
| case_type | Category | VARCHAR(30) | N |  | ACH Fraud | Account Takeover, ACH Fraud, Wire Fraud, Identity Review, Card Fraud. |
| alert_source | Category | VARCHAR(30) | N |  | ML Model | ML Model, Member Report, Operations Review, Rules Engine. |
| case_status | Category | VARCHAR(15) | N |  | Closed | Open, Investigating, Escalated, Closed. |
| priority | Category | VARCHAR(10) | N |  | High | Low, Medium, High, Critical. |
| suspected_loss_amount | Currency amount | DECIMAL(15,2) | N |  | "$1,060.33 " | Strip $, commas, spaces. |
| confirmed_loss_amount | Currency amount | DECIMAL(15,2) | N |  | $299.50  | Strip $, commas, spaces. 0 until confirmed. |
| assigned_queue | Category | VARCHAR(30) | N |  | Digital Fraud | Deposit Ops, Digital Fraud, Enhanced Review, Card Ops. |
| resolution_code | Category | VARCHAR(20) | Y |  | Confirmed Fraud | Confirmed Fraud, False Positive; blank unless Closed. |
| case_close_ts | Timestamp | TIMESTAMP | Y |  | 8/4/2026 16:00 | Blank unless Closed. US Eastern (ET). |

### 5.2 Reference: member_360 (lookup only)

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| member_id | Identifier | VARCHAR(10) | N | PK | M000001 | Published by DP_Member_360. |

### 5.3 Reference: account ID mapping table (data/reference/account_id_map.csv)

- Shared reference data (SCRUM-32), built and validated by tools/build_account_id_map.py and tools/validate_account_id_map.py.
- One row per (source_system, source_account_id): one-to-one within a system, many-to-one across systems.
- Fraud Case reads the fraud_case_mgmt rows to set account_found_flag.

| Column | Logical type | Physical type | Null? | Key | Example (raw) | Description / conversion rule |
|---|---|---|---|---|---|---|
| source_system | Category | VARCHAR(30) | N | PK | fraud_case_mgmt | System the ID comes from. |
| source_account_id | Identifier | VARCHAR(12) | N | PK | A0000001 | Account ID as that system writes it. |
| account_id | Identifier | VARCHAR(10) | N |  | A0000001 | Canonical ^A\d{7}$ (zero-padded: A0001, A00001 → A0000001). |
| in_core_banking | Boolean | BOOLEAN | N |  | TRUE | Canonical ID exists in core banking. |
| mapping_rule | Category | VARCHAR(40) | N |  | pad_to_7_digits | Rule used to derive account_id. |

## 6. Target data product: fraud_case

- Grain: one row per case.
- Primary key: case_id.
- Refresh: daily full rebuild.
- Column order: the 13 sample columns, then the derived columns, then the audit columns.

| Column | Logical type | Physical type | Null? | Key | Allowed values / format | Description |
|---|---|---|---|---|---|---|
| case_id | Identifier | VARCHAR(10) | N | PK | ^FC\d{7}$ | Fraud case ID. |
| member_id | Identifier | VARCHAR(10) | N |  | ^M\d{6}$ | Member on the case. |
| primary_account_id | Identifier | VARCHAR(10) | N |  | ^A\d{7}$ | Primary account on the case. |
| case_open_ts | Timestamp | TIMESTAMP | N |  | YYYY-MM-DD HH:MM:SS | When the case opened. |
| case_type | Category | VARCHAR(30) | N |  | Account Takeover, ACH Fraud, Wire Fraud, Identity Review, Card Fraud | Fraud type. |
| alert_source | Category | VARCHAR(30) | N |  | ML Model, Member Report, Operations Review, Rules Engine | What raised the alert. |
| case_status | Category | VARCHAR(15) | N |  | Open, Investigating, Escalated, Closed | Case lifecycle status. |
| priority | Category | VARCHAR(10) | N |  | Low, Medium, High, Critical | Case priority. |
| suspected_loss_amount | Currency amount | DECIMAL(15,2) | N |  | ≥ 0 | Loss suspected at intake. |
| confirmed_loss_amount | Currency amount | DECIMAL(15,2) | N |  | 0 ≤ x ≤ suspected | Loss confirmed at close. |
| assigned_queue | Category | VARCHAR(30) | N |  | Deposit Ops, Digital Fraud, Enhanced Review, Card Ops | Work queue. |
| resolution_code | Category | VARCHAR(20) | Y |  | Confirmed Fraud, False Positive | Set only when Closed. |
| case_close_ts | Timestamp | TIMESTAMP | Y |  | ≥ case_open_ts | Set only when Closed. |
| is_closed | Boolean | BOOLEAN | N |  | TRUE / FALSE | case_status = Closed. |
| days_to_close | Duration (days) | DECIMAL(7,2) | Y |  | ≥ 0; closed only | Time to resolve. |
| case_age_days | Integer | INT | Y |  | ≥ 0; open only | Age at run date. |
| loss_confirmation_ratio | Ratio | DECIMAL(5,4) | Y |  | 0–1; closed only | Share of suspected loss confirmed. |
| member_found_flag | Boolean | BOOLEAN | N |  | TRUE / FALSE | Member exists in member_360. |
| account_found_flag | Boolean | BOOLEAN | N |  | TRUE / FALSE | Account exists in core banking (via account_id_map). |
| sla_days | Integer | INT | N |  | 30 / 45 / 60 / 90 by priority | SLA for the case priority (configurable). |
| sla_breached_flag | Boolean | BOOLEAN | N |  | TRUE / FALSE | Elapsed days (to close, or age if open) > sla_days. |
| dp_load_ts | Timestamp | TIMESTAMP | N |  | YYYY-MM-DD HH:MM:SS | Load time. |
| dp_batch_id | Identifier | VARCHAR(36) | N |  | UUID | Pipeline run ID. |

## 7. Source-to-target mapping

| Target column | Source | Rule | Status |
|---|---|---|---|
| case_id | DP_Fraud_Case.case_id | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| member_id | DP_Fraud_Case.member_id | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| primary_account_id | DP_Fraud_Case.primary_account_id | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| case_open_ts | DP_Fraud_Case.case_open_ts | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| case_type | DP_Fraud_Case.case_type | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| alert_source | DP_Fraud_Case.alert_source | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| case_status | DP_Fraud_Case.case_status | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| priority | DP_Fraud_Case.priority | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| suspected_loss_amount | DP_Fraud_Case.suspected_loss_amount | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| confirmed_loss_amount | DP_Fraud_Case.confirmed_loss_amount | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| assigned_queue | DP_Fraud_Case.assigned_queue | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| resolution_code | DP_Fraud_Case.resolution_code | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| case_close_ts | DP_Fraud_Case.case_close_ts | Type per dictionary; validate allowed values / pattern. | Mapped (direct) |
| is_closed | case_status | case_status == 'Closed'. | Mapped (rule) |
| days_to_close | case_open_ts, case_close_ts | Round((close - open) seconds / 86400, 2); NULL if not closed. | Mapped (rule) |
| case_age_days | case_open_ts + run date | Whole days from open_ts to run date; NULL if closed. | Mapped (rule) |
| loss_confirmation_ratio | confirmed_loss_amount, suspected_loss_amount | Round(confirmed / suspected, 4); NULL if not closed or suspected = 0. | Mapped (rule) |
| member_found_flag | member_360.member_id | member_id IN member_360. Unmatched rows are kept and reported. | Mapped (lookup) |
| account_found_flag | account_id_map (fraud_case_mgmt rows) | in_core_banking for primary_account_id; FALSE if unmapped. Kept and reported. | Mapped (lookup) |
| sla_days | priority | Settings.sla_days_by_priority[priority]. | Mapped (rule) |
| sla_breached_flag | days_to_close / case_age_days, sla_days | Closed: days_to_close > sla_days; open: case_age_days > sla_days. | Mapped (rule) |
| dp_load_ts / dp_batch_id | pipeline | Audit columns. | Mapped (pipeline) |

## 8. Functional requirements

| ID | Requirement | Description |
|---|---|---|
| FR-01 | Ingest case extract | Load DP_Fraud_Case.csv unchanged into raw, adding file name, load time and batch ID. |
| FR-02 | Standardize data types | Convert every column to its section-5 type; bad values and duplicate case_ids go to rejects. |
| FR-03 | Case lifecycle and loss checks | Enforce the lifecycle and loss rules (DQ-06 to DQ-11); reject broken cases with a reason. |
| FR-04 | Link to Member 360 | Flag member_found_flag; keep unmatched cases and report them; DQ-14 match-rate gate (off by default). |
| FR-05 | Derived case metrics | Calculate is_closed, days_to_close, case_age_days, loss_confirmation_ratio, sla_days and sla_breached_flag. |
| FR-06 | Publish, exceptions and govern | Publish the table, CSV, data contract (timezone ET) and DDL; exceptions; daily status snapshot; block publish on critical failures. |
| FR-07 | Account ID mapping (SCRUM-32) | Shared reference table maps every system's account ID to canonical A + 7 digits; set account_found_flag. |

### User stories

- As a fraud ops lead, I want open-case age and priority, so that I can chase critical cases past SLA.
- As a finance analyst, I want typed suspected and confirmed losses, so that loss reporting is consistent.
- As a compliance officer, I want every Closed case to have a close date and resolution, so that the audit trail is complete.
- As an analyst, I want member_found_flag, so that I know which cases join to Member 360.

## 9. Non-functional requirements

- Daily batch, ready by 07:00 ET; idempotent reruns.
- No PII beyond pseudonymous IDs (no names, notes or investigator details).
- Lineage via dp_batch_id; run log with rows in/out/rejected.
- A blocking DQ failure keeps the previous published table.

## 10. Data quality rules and acceptance criteria

| Rule | Check | Severity |
|---|---|---|
| DQ-01 | case_id unique and not null | Critical – block |
| DQ-02 | case_id, member_id, primary_account_id match their patterns | Critical – block |
| DQ-03 | All NOT NULL columns populated | Critical – block |
| DQ-04 | Category columns only contain allowed values | Critical – block |
| DQ-05 | Product rows = source cases (reconciliation) | Critical – block |
| DQ-06 | Closed ⇔ case_close_ts and resolution_code are both present | High – reject row |
| DQ-07 | case_close_ts ≥ case_open_ts | High – reject row |
| DQ-08 | 0 ≤ confirmed_loss ≤ suspected_loss | High – reject row |
| DQ-09 | False Positive or not-closed cases have confirmed_loss = 0 | Medium – warn |
| DQ-10 | Confirmed Fraud has confirmed_loss > 0 | Medium – warn (switchable to reject) |
| DQ-11 | case_open_ts not after the run date | High – reject row |
| DQ-12 | member_id found in member_360 | Medium – warn (row kept, flagged) |
| DQ-13 | assigned_queue allowed for case_type (only when a routing matrix is configured) | Medium – warn |
| DQ-14 | Member match rate ≥ configured minimum (default 0 = never blocks) | Critical – block |

### Acceptance criteria (release)

- All 23 target columns present, with the physical types in section 6.
- Open cases past SLA reported as CASE_SLA_BREACHED (27 at 2026-10-04: Critical 15, High 9, Medium 3).
- 90 cases flagged account_found_flag FALSE and reported as ACCOUNT_NOT_FOUND.
- All critical DQ rules pass on the sample; 100 rows published.
- Derived metrics match hand-calculated examples (e.g. FC0000002: 3.00 days, ratio 0.8000).
- 90 unmatched members appear in the exception report (sample member_360 has 10 members).

## 11. Open questions and data gaps

- All seven questions now have a decision (OpenSpec change resolve-fraud-case-open-decisions). Items marked 'sign-off' are configurable defaults awaiting confirmation.

| # | Finding (verified against sample) | Decision | Status |
|---|---|---|---|
| Q1 | member_id M000001–M000100; today's member_360 has only M000001–M000010. | Keep and flag; DQ-14 records the match rate and blocks below Settings.min_member_match_rate (default 0). Raise once Member 360 has the full feed. | Decided |
| Q2 | primary_account_id is A + 7 digits (A0000001); banking sources use A + 5 (A00001). | Canonical A + 7 digits via data/reference/account_id_map.csv (SCRUM-32); account_found_flag + ACCOUNT_NOT_FOUND. | Decided |
| Q3 | Timestamps have no time zone (hours are only 00:00, 08:00 and 16:00). | US Eastern (America/New_York), no offset; declared in the data contract. | Decided |
| Q4 | assigned_queue rotates evenly regardless of case_type (e.g. Card Fraud → Deposit Ops). | Not enforced; optional DQ-13 warning once Fraud Ops supplies a routing matrix. | Decided – matrix pending |
| Q5 | All 60 non-closed cases are 30–63 days old at 2026-10-04; 15 are Critical. | SLA by priority: Critical 30, High 45, Medium 60, Low 90 days; CASE_SLA_BREACHED replaces CRITICAL_CASE_AGED (BREAKING). | Decided – Fraud Ops sign-off |
| Q6 | Confirmed Fraud with $0 loss: none in sample (all 27 have a loss, ratio 0.35–0.80). | Warn (DQ-10): fully recovered funds can leave $0 loss; switch to reject in Settings if needed. | Decided |
| Q7 | Only current status in the extract; no status history. | Daily fraud_case_status_snapshot (one row per case per run date); history from go-live. | Decided |

## 12. Dependencies, risks and milestones

- Depends on DP_Member_360's published member_360 for the member lookup.
- Case-management extract delivered daily.

| Risk | Mitigation |
|---|---|
| Member 360 incomplete | Keep and flag cases; report the match rate. |
| Extract format changes | Header check fails fast (FR-01). |

| Milestone | Content | Est. |
|---|---|---|
| M1 | FR-01, FR-02: ingest + types | Sprint 1 |
| M2 | FR-03, FR-05: lifecycle DQ + metrics | Sprint 1 |
| M3 | FR-04, FR-06: member link + publish | Sprint 2 |

## 13. Appendix – sources

- data/raw/DP_Fraud_Case.csv — 100 rows, columns: case_id, member_id, primary_account_id, case_open_ts, case_type, alert_source, case_status, priority, suspected_loss_amount, confirmed_loss_amount, assigned_queue, resolution_code, case_close_ts
- data/product/DP_Fraud_Case.csv — identical copy, used as the target sample.
- output/DP_Member_360/04_code/out/member_360.csv — member lookup.
- data/reference/account_id_map.csv — 110 rows, account ID mapping reference table.
- Profile (verified): 40 Closed (27 Confirmed Fraud, 13 False Positive), 60 not closed; suspected total $371,309.50; confirmed total $54,753.40; days to close 1–12 (avg 6.3).
