# Spec Delta

## Purpose

Defines how the Account Daily Balance data product is published: the DQ gate, exception report, data contract, DDL and PII handling.

## ADDED Requirements

### Requirement: Published CSV follows the sample column order
The published CSV SHALL start with the 11 sample columns in sample order, followed by the remaining contract columns in contract order.

#### Scenario: Header order
- **WHEN** a run publishes
- **THEN** the CSV header's first 11 columns equal the sample columns, and the full header equals the contract's column order

### Requirement: Critical DQ rules block publishing
DQ-01 to DQ-07 and DQ-10 SHALL be blocking rules. When any of them fails, the run SHALL be BLOCKED and SHALL NOT replace the product table, the product CSV or the data contract, so the previous product stays.

#### Scenario: Balance equation fails
- **WHEN** a row's closing balance is not opening + credits − debits
- **THEN** DQ-05 fails, the run is BLOCKED and the previously published product is unchanged

#### Scenario: Reconciliation fails
- **WHEN** an account's credits − debits differ from its counted source transactions
- **THEN** DQ-07 fails and the run is BLOCKED

#### Scenario: First run blocked
- **WHEN** the first run is BLOCKED
- **THEN** no product CSV or data contract is written

### Requirement: Exception report lists rejects and warnings with rule ID
Every run SHALL write an exception report containing one row per rejected row and one row per warning, each with its DQ rule ID.

#### Scenario: Reject and warning reported
- **WHEN** an upstream DQ-08 reject is passed in and a row has available_balance above closing_balance
- **THEN** the report has a REJECT row with rule DQ-08 and a WARN row with rule DQ-11

### Requirement: DDL is generated from the contract
The committed DDL SHALL be generated from the contracts and SHALL be checked against them by a test.

#### Scenario: DDL in sync
- **WHEN** the tests run
- **THEN** each committed `sql/ddl` file equals the DDL generated from its contract

### Requirement: Rerun is idempotent
A rerun with the same inputs SHALL produce the same product rows, apart from the batch ID.

#### Scenario: Two runs
- **WHEN** publish runs twice with the same inputs
- **THEN** the product rows are equal apart from `dp_batch_id`, and the table holds one copy

### Requirement: No PII is published
The product contract SHALL have no PII column. Every value in a PII-named column (names, addresses, postal codes) SHALL be replaced with `*` before anything is written, and a reject on a PII column SHALL have its raw value masked and its reason rewritten so it quotes no value, keeping the rule ID.

#### Scenario: PII column reaches publish
- **WHEN** the product frame carries `first_name` and `postal_code`
- **THEN** their values are masked with `*`, and neither column appears in the product table or CSV

#### Scenario: PII reject value
- **WHEN** an upstream reject has column `postal_code`
- **THEN** its raw value is stored as `*`, and neither the rejects table nor the exception report contains the value
