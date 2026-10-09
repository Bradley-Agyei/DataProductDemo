# Proposal

## Why

DP_Fraud_Case (SCRUM-25) shipped with seven open decisions (PRD section 11, Q1–Q7), so parts of its behaviour are placeholders:
- 90 of 100 cases can't be linked to a member.
- No case can be linked to an account.
- Timestamps have no declared time zone.
- Only Critical cases have an SLA.
- There's no status history.

Settling these now, while the product has one consumer and a 100-row sample, is cheap. After consumers build on the placeholders it gets expensive.

## What Changes

Each open question gets a decision:

- **Q1 – Member coverage.** Keep-and-flag stays the rule for unmatched members.
  - Add a **member match rate** to each run's DQ results.
  - Add a configurable minimum match rate. Default 0, so it's off until Member 360 receives the full member feed. Below the minimum, the run is blocked.
- **Q2 – Account ID standard (Jira SCRUM-32).** The canonical account ID is `A` + 7 digits. Any source width converts to it (`A0001`, `A00001` → `A0000001`).
  - A governed **account ID mapping reference table**, `data/reference/account_id_map.csv`, maps each (source system, source ID) to the canonical ID and flags whether the account exists in core banking. Several systems may map to the same canonical ID; within one system the mapping is one-to-one.
  - DP_Member_360 validates its core banking accounts against the table.
  - DP_Fraud_Case gets `account_found_flag BOOLEAN` and an `ACCOUNT_NOT_FOUND` exception. Unmatched cases are kept.
- **Q3 – Time zone.** All case timestamps are **US Eastern local time (America/New_York)**, stored without an offset.
  - The data contract gains a `timezone` field, and timestamp column descriptions say "ET".
  - No values change.
- **Q4 – Queue routing.** The product does not enforce routing.
  - An optional case-type → allowed-queues matrix (off by default) turns on a warning rule, **DQ-13**, once Fraud Ops supplies the matrix.
- **Q5 – SLA per priority.** Proposed defaults: **Critical 30, High 45, Medium 60, Low 90 days**, configurable. These need Fraud Ops sign-off.
  - New product columns: `sla_days INT` and `sla_breached_flag BOOLEAN`. These apply to closed cases (days to close) and open cases (age).
  - **BREAKING:** the exception `CRITICAL_CASE_AGED` is replaced by `CASE_SLA_BREACHED`, which covers all priorities. Only open cases are reported.
- **Q6 – Confirmed Fraud with $0 loss.** Stays a **warning** (DQ-10), because funds that are fully recovered can legitimately leave a $0 loss. The decision is recorded and the setting stays.
- **Q7 – Status history.** Add an append-only `fraud_case_status_snapshot` table: one row per case per run date, idempotent per date. Time spent in each status can be measured from the go-live date onwards.
- The PRDs, data dictionaries, stories and Jira (SCRUM-25 and its stories) are updated to show each question as **Decided**.

## Capabilities

### New Capabilities
- `identity/account-id-conformance`: the canonical account ID format, converting source account IDs of any width to it, and the account ID mapping reference table that other products use for lookups.
- `data-products/fraud-case`: the fraud case product's behaviour. This covers lifecycle and loss rules, the time zone convention, member and account linkage, SLA by priority, the optional routing check and the status snapshot history.

### Modified Capabilities
- None. No specs exist yet in `openspec/specs/`.

## Impact

- **DP_Fraud_Case** (`output/DP_Fraud_Case/04_code`):
  - contracts: +3 product columns, a new snapshot table, contract metadata
  - `config.Settings`: SLA map, minimum match rate, routing matrix
  - `transform.py`, `dq_rules.py` (DQ-12 match rate, DQ-13), `exceptions.py`, `run.py`
  - tests and DDL
- **Reference data:** `data/reference/account_id_map.csv` (already built: 110 rows, from `Account.csv` and `DP_Fraud_Case.csv`), plus a generator and validator for it.
- **DP_Member_360** (`output/DP_Member_360/04_code`): account ID conversion function, a check that every core banking account appears in the reference table, and tests.
- **Cross-product dependency:** the fraud case product reads `account_id_map.csv` alongside `member_360.csv`. Its tests use checked-in copies of both files.
- **Docs and tracking:** PRD section 11, the data dictionaries, `stories.md`, the test report, Jira comments, and the GitHub branches (SCRUM-17 and SCRUM-25 need follow-up commits).
- **Consumers:** the `dq_exceptions` exception types change (**BREAKING** for anyone filtering on `CRITICAL_CASE_AGED`).
