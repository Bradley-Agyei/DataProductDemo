# Spec Delta

## Purpose

Keeps the account_daily_balance product contract aligned with PRD_Account_Daily_Balance.md §6.

## ADDED Requirements

### Requirement: Product contract follows the PRD
The account_daily_balance contract SHALL match PRD §6, read from the PRD file: column order and physical types, the primary key (`account_id`, `balance_date`), the allowed values of `product_code` and `account_status`, and the 11 sample columns at the start.

#### Scenario: PRD and contract agree
- **WHEN** the tests run
- **THEN** every contract check against §6 passes

#### Scenario: PRD changes a type
- **WHEN** PRD §6 changes a column's physical type and the contract does not
- **THEN** the column test fails
