# Proposal

## Why

DP_Account_Daily_Balance (Jira epic SCRUM-35) must reach consumers only when it passes its checks, so a broken balance is never read. FR-07 (Jira SCRUM-43, PRD §8 FR-07, §10) is the publish step: the DQ gate, the exception report, the data contract and the DDL.

## What Changes

- A new product folder, `output/DP_Account_Daily_Balance/04_code/`, on the shared `dp_framework`. Its framework copy is byte-identical to the other products'.
- The contract `account_daily_balance`, with the 15 columns from PRD §6. The key is `balance_date` + `account_id`. `product_code` (Q6) and `available_balance` (Q5) are pending.
- `publish()`: it masks PII with `*`, runs the critical DQ gate (DQ-01 to 07 and DQ-10, which block) and the DQ-11 warning, then writes:
  - every run: rejects, DQ results, the exception report and the run log;
  - on SUCCESS only: the product table, the CSV and the data contract.
- DDL is generated from the contracts into `sql/ddl/`, and a test keeps it in sync.

Out of scope: FR-01 to FR-06 (SCRUM-37 to 42). They build the product frame and the counted transactions that `publish` takes. The story's end-to-end verify step (sample run, 100 rows) waits for them.

## Source

`output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md` (Draft v0.1) is added in this change. The contract follows PRD §6 and the DQ rules follow §10:
- DQ-07 reconciles credits and debits separately.
- The 11 sample columns are the first 11 columns in §6.

## Capabilities

### New Capabilities
- `data-products/account-daily-balance`: publishing the Account Daily Balance product behind a DQ gate.

## Impact

- New: `output/DP_Account_Daily_Balance/04_code/`, `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md` and `docs/kt/account-daily-balance/README.md`.
- No change to the other products or to `dp_framework`.
