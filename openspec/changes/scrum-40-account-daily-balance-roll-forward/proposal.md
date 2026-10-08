# Proposal

## Why

DP_Account_Daily_Balance (Jira epic SCRUM-35) promises a finance controller balances that reconcile day to day. FR-04 (Jira SCRUM-40, PRD §8 FR-04) is the roll-forward: one row per account per calendar day, where each day opens at the previous day's closing and closes at opening + credits − debits.

## What Changes

- `src/account_daily_balance/roll_forward.py`:
  - `calendar_spine(accounts, dates)`: every Date row × every account open on that day.
  - `roll_forward(accounts, dates, daily_totals)`: opening, totals and closing for every spine row. Days without activity carry the balance.
- `config.FIRST_DAY_OPENING_COLUMN`: the Account column used as the first day's opening (Q2).
- Tests:
  - unit tests on hand-built frames;
  - sample acceptance tests that build daily totals from `data/raw` through a test-only loader.

Out of scope:
- FR-01 to FR-03 (SCRUM-37 to 39). They produce the typed accounts and the daily totals.
- FR-05 and FR-06 (SCRUM-41, 42).
- Wiring the steps into `publish`.

`sample_inputs.py` in the tests stands in for FR-01 to FR-03 until SCRUM-39 lands. It counts Posted transactions only, which is the PRD's Q4 default.

## Source

- Jira SCRUM-40.
- PRD `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md`: §7 mapping, §8 FR-04, DQ-05 and DQ-06. The PRD is not on `develop` yet; it is in commit 888ad16 on `feature/SCRUM-43-prd-and-dq07`.

## Open questions, implemented as the PRD's proposed decisions

- **Q2** (Finance confirm): `Account.current_balance` is the opening balance of the first day.
- **Q3** (source owner confirm): `Transaction.balance_after` is ignored and balances are recomputed. `roll_forward` takes daily totals, never transactions, so `balance_after` cannot reach it.
- **Q7** (PO confirm): one row per account per calendar day, 10 × 10 = 100 on the sample, with balances carried forward.

## Interface for FR-03

`daily_totals` has one row per account per day with activity:
- `account_id` and `balance_date` (DATE);
- `total_credits` and `total_debits`, as `Decimal` and both non-negative.

Any other columns, such as `transaction_count` and `pending_debits`, are passed through. They become 0 on days with no activity.

## Capabilities

### Modified Capabilities
- `data-products/account-daily-balance`: adds the balance roll-forward.

## Impact

- New: `roll_forward.py`, `tests/sample_inputs.py`, `tests/test_roll_forward.py`.
- Changed:
  - `config.py`: Q2 setting and Jira reference;
  - `04_code/README.md` and `docs/kt/account-daily-balance/README.md`.
- No change to the contract, DDL, `publish` or `dp_framework`.
