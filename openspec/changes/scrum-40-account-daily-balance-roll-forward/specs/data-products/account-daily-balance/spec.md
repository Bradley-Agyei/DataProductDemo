# Spec Delta

## Purpose

Defines the Account Daily Balance roll-forward: which rows exist, and how opening and closing balances chain from day to day.

## ADDED Requirements

### Requirement: One row per account per calendar day
The roll-forward SHALL produce exactly one row for every Date row × every account whose open date is on or before that day, whether or not the account had activity.

#### Scenario: Sample calendar
- **WHEN** the roll-forward runs on the sample (10 accounts, 10 Date rows, all accounts opened before the first day)
- **THEN** it returns 100 rows and `account_id` + `balance_date` is unique

#### Scenario: Account opened mid-calendar
- **WHEN** an account's open date is after the first Date row
- **THEN** it has no rows before its open date

#### Scenario: Activity outside the calendar
- **WHEN** daily totals hold a row for a day the account has no spine row
- **THEN** the roll-forward fails instead of dropping the activity

### Requirement: Opening balance chains from the previous day
An account's first row SHALL open at `Account.current_balance` (Q2). Every later row SHALL open at the previous day's closing balance (DQ-06).

#### Scenario: First day
- **WHEN** A0000001 is rolled forward on the sample
- **THEN** 2026-09-21 opens at 500.00

#### Scenario: Next day
- **WHEN** A0000001 closes 2026-09-21 at 10,713.32
- **THEN** 2026-09-22 opens at 10,713.32

### Requirement: Closing balance is opening plus credits minus debits
Every row SHALL close at opening + total credits − total debits (DQ-05). A day without activity SHALL have 0.00 credits and debits and carry its opening balance.

#### Scenario: Day with credits
- **WHEN** A0000001 has 10,213.32 in counted credits on 2026-09-21
- **THEN** it closes at 10,713.32

#### Scenario: Day without activity
- **WHEN** an account has no counted transactions on a day
- **THEN** its credits and debits are 0.00 and its closing equals its opening

#### Scenario: DQ rules on the sample
- **WHEN** DQ-05 and DQ-06 run on the sample roll-forward
- **THEN** no row fails

### Requirement: Source running balance is not used
The roll-forward SHALL NOT read `Transaction.balance_after` (Q3); balances SHALL come only from the opening balance and the counted daily totals.

#### Scenario: balance_after changes
- **WHEN** every `balance_after` value in the source transactions is changed
- **THEN** the roll-forward output is identical
