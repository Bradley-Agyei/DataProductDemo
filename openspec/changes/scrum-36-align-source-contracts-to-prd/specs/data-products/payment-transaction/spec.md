# Spec Delta

## Purpose

Keeps the Payment Transaction source contracts and raw-layer PII handling aligned with PRD_Payment_Transaction.md §5.

## ADDED Requirements

### Requirement: Source contracts follow the PRD
Each of the 7 source contracts SHALL list its columns in file order, with the physical type and key that PRD §5 gives them. The check SHALL read §5 from the PRD file, not from a copy.

#### Scenario: Contract drifts from the PRD
- **WHEN** a source contract column's type or key differs from PRD §5
- **THEN** the source contract test fails, naming the table

### Requirement: Raw key integrity is verified, not repaired
The test suite SHALL check the read-only raw extracts for unique primary keys, the PRD §5 raw ID formats, resolving foreign keys, transactions matching their account's owner and branch, transaction direction matching its type, every account being present in `account_id_map`, and `date_key` agreeing with `full_date`. Foreign keys to files outside the 7 sources (`Account.product_id` → `Product.csv`) SHALL be checked too. A failure SHALL be reported as a source finding, and `data/raw/` SHALL NOT be edited.

#### Scenario: Sample extracts
- **WHEN** the tests run on the committed sample extracts
- **THEN** every key integrity check passes

#### Scenario: Orphan key in a new extract
- **WHEN** a transaction references an account that is not in Account.csv
- **THEN** the foreign key test fails, listing the orphan key value

### Requirement: Every PII column the PRD hides is masked
The raw layer SHALL mask every Member column that PRD §5.7 marks as PII (`first_name`, `last_name`, `city`, `postal_code`), and the Branch columns §5.5 hides as matching member PII (`city`, `postal_code`), by replacing each value with `*` before anything is written.

#### Scenario: City is masked
- **WHEN** the run loads the sample extracts
- **THEN** every value of `raw_member.city` and `raw_branch.city` is `*`
