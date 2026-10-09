# fraud-case Specification

## Purpose
Defines the behaviour of the governed fraud case data product: one typed row per case, with lifecycle and loss rules, links to members and accounts, SLA tracking and status history.

## Requirements

### Requirement: Case timestamps are US Eastern local time
All case timestamps (`case_open_ts`, `case_close_ts`) SHALL be interpreted and published as US Eastern local time (America/New_York) without an offset. The published data contract SHALL state this time zone.

#### Scenario: Data contract declares the time zone
- **WHEN** the product is published
- **THEN** the data contract includes `timezone: America/New_York` and each timestamp column description states ET

#### Scenario: Values are not shifted
- **WHEN** the extract contains `8/1/2026 8:00` for a case
- **THEN** the published `case_open_ts` is `2026-08-01 08:00:00`

### Requirement: Case lifecycle is consistent
A case SHALL be Closed if and only if it has both a close timestamp and a resolution code. Its close time SHALL NOT be before its open time, and it SHALL NOT be opened after the run date. A case violating any of these SHALL be rejected with the rule ID and SHALL NOT be published.

#### Scenario: Closed case missing its close time
- **WHEN** a case has status Closed but no `case_close_ts`
- **THEN** the case is rejected with DQ-06 and the run still publishes the remaining cases

#### Scenario: Close before open
- **WHEN** a case's `case_close_ts` is earlier than its `case_open_ts`
- **THEN** the case is rejected with DQ-07

### Requirement: Confirmed loss stays within suspected loss
Confirmed loss SHALL be between 0 and the suspected loss, inclusive. A case outside that range SHALL be rejected with DQ-08.

#### Scenario: Confirmed exceeds suspected
- **WHEN** a case has suspected loss 374.38 and confirmed loss 399.50
- **THEN** the case is rejected with DQ-08

### Requirement: Confirmed Fraud with zero loss is a warning
A Confirmed Fraud case with a confirmed loss of 0 SHALL be published and recorded as a DQ-10 warning, because fully recovered funds can legitimately leave no loss. The severity SHALL be configurable so it can be changed to reject without changing code.

#### Scenario: Default behaviour keeps the case
- **WHEN** a Confirmed Fraud case has confirmed loss 0 and the default configuration is used
- **THEN** the case is published and DQ-10 has status Warn

#### Scenario: Configured to reject
- **WHEN** the DQ-10 severity is configured as reject
- **THEN** that case is rejected with DQ-10

### Requirement: Cases are linked to members without dropping cases
Each published case SHALL carry `member_found_flag`, TRUE when its member ID exists in the Member 360 published product. Unmatched cases SHALL be published, flagged FALSE and reported as `MEMBER_NOT_FOUND` exceptions.

#### Scenario: Member 360 has 10 of 100 members
- **WHEN** the product runs on the 100-case sample while Member 360 publishes `M000001`–`M000010`
- **THEN** all 100 cases are published, 10 have `member_found_flag` TRUE, and 90 `MEMBER_NOT_FOUND` exceptions are reported

### Requirement: Member match rate is measured and can gate publishing
Each run SHALL record a DQ-14 result stating the member match rate (matched cases / published cases) and the configured minimum. When the rate is below a configured minimum, DQ-14 SHALL fail and block the run. The default minimum SHALL be 0, which never blocks.

#### Scenario: Default minimum never blocks
- **WHEN** the match rate is 10% and no minimum is configured
- **THEN** the run publishes, DQ-14 has status Pass, and its description states a 10.00% match rate

#### Scenario: Configured minimum blocks the run
- **WHEN** the configured minimum match rate is 99% and the actual rate is 10%
- **THEN** the run is blocked and the previously published product remains unchanged

### Requirement: Cases are linked to accounts without dropping cases
Each published case SHALL carry `account_found_flag BOOLEAN`. It is TRUE when the mapping reference table maps the case's `primary_account_id` (source system `fraud_case_mgmt`) to a canonical ID that exists in core banking. Unmatched cases SHALL be published, flagged FALSE and reported as `ACCOUNT_NOT_FOUND`.

#### Scenario: Core banking holds 10 of 100 accounts
- **WHEN** the reference table maps `A0000001`–`A0000010` to accounts that exist in core banking
- **THEN** case FC0000001 (`A0000001`) has `account_found_flag` TRUE, case FC0000011 (`A0000011`) has FALSE, and 90 `ACCOUNT_NOT_FOUND` exceptions are reported

#### Scenario: Reference table missing
- **WHEN** the account ID mapping reference table cannot be found
- **THEN** the run fails before publishing with a message naming the missing file

### Requirement: SLA is set by priority
Each published case SHALL carry `sla_days INT`, the SLA for its priority. The defaults are Critical 30, High 45, Medium 60 and Low 90 days, and they SHALL be configurable.

#### Scenario: SLA assigned from priority
- **WHEN** a case has priority High
- **THEN** its `sla_days` is 45 under the default configuration

### Requirement: SLA breach is flagged for open and closed cases
Each case SHALL carry `sla_breached_flag BOOLEAN`. A closed case is breached when `days_to_close` exceeds `sla_days`. An open case is breached when `case_age_days` exceeds `sla_days`. Every breached open case SHALL be reported as a `CASE_SLA_BREACHED` exception.

#### Scenario: Open Critical case past SLA
- **WHEN** case FC0000011 (Critical, Investigating) is 60 days old at run date 2026-10-04
- **THEN** `sla_breached_flag` is TRUE and a `CASE_SLA_BREACHED` exception is reported for it

#### Scenario: Closed case within SLA
- **WHEN** case FC0000002 (High, Closed) took 3.00 days to close
- **THEN** `sla_breached_flag` is FALSE and no exception is reported for it

#### Scenario: Former critical-only exception no longer emitted
- **WHEN** the product runs
- **THEN** no exception of type `CRITICAL_CASE_AGED` is produced

### Requirement: Queue routing check is optional
When a case-type-to-allowed-queues matrix is configured, every case whose assigned queue is not allowed for its case type SHALL be recorded as a DQ-13 warning, and the case SHALL still be published. When no matrix is configured, DQ-13 SHALL be recorded as Pass, with zero rows checked.

#### Scenario: No matrix configured
- **WHEN** the product runs with the default configuration
- **THEN** DQ-13 has status Pass and 0 rows checked

#### Scenario: Matrix flags an unexpected queue
- **WHEN** the matrix allows only Card Ops for Card Fraud and case FC0000005 (Card Fraud) is in Deposit Ops
- **THEN** DQ-13 has status Warn, counts FC0000005 as a failure, and FC0000005 is still published

### Requirement: Case status history is kept
Each successful run SHALL append one status snapshot per published case, keyed by case ID and run date, containing status, priority and assigned queue. Rerunning the same run date SHALL replace that date's snapshot rows rather than duplicate them.

#### Scenario: Two run dates build history
- **WHEN** the product runs successfully for 2026-10-04 and then for 2026-10-05
- **THEN** the snapshot table holds 200 rows, 100 per run date

#### Scenario: Same-date rerun is idempotent
- **WHEN** the product runs twice for 2026-10-04
- **THEN** the snapshot table holds exactly 100 rows for 2026-10-04
