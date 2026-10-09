# Spec Delta

## Purpose

Defines FR-02 source type conversion, identifier conformance, and row rejects
for DP_Account_Daily_Balance.

## ADDED Requirements

### Requirement: Source extracts are standardized to PRD types
The standardization step SHALL return typed Account, Transaction,
Transaction_Type, Product, Member, and Date frames using the PRD §5 physical
types. Currency text SHALL accept currency symbols, separators, surrounding
spaces, and parenthesized negatives. Date text SHALL be converted to DATE and
date keys SHALL be eight-digit integers in `YYYYMMDD` form.

#### Scenario: Accounting currency is parsed
- **WHEN** a currency column contains `($199.78)`
- **THEN** the typed value is decimal `-199.78`

#### Scenario: Dates and date keys are parsed
- **WHEN** `open_date` or `full_date` contains a valid M/D/YYYY date
- **THEN** it is returned as a date; an eight-digit `date_key` is returned as an integer

#### Scenario: Invalid source value
- **WHEN** any required source value cannot be parsed or violates its source contract
- **THEN** the source row is excluded from the typed frame and a reject identifies its table, key,
  column, raw value, and reason

### Requirement: Identifiers are conformed before downstream use
Account identifiers SHALL be mapped through `account_id_map` using only
`core_banking` rows marked as present in core banking. Every typed account ID
SHALL match `^A\d{7}$`. Member identifiers SHALL be conformed to
`^M\d{6}$` by left-padding the numeric portion.

#### Scenario: Source account maps to canonical ID
- **WHEN** a core banking source account has a canonical mapping
- **THEN** the typed Account or Transaction row contains that canonical ID

#### Scenario: Account mapping is missing
- **WHEN** a source account has no eligible core banking mapping
- **THEN** its row is excluded and the reject reason is exactly `DQ-08`

#### Scenario: Member identifier is short
- **WHEN** a member identifier is `M0001`
- **THEN** the typed member identifier is `M000001`

### Requirement: Duplicate business keys are rejected
Every copy of a duplicate source primary key SHALL be excluded from the typed
frame and SHALL have a reject with a clear duplicate-key reason.

#### Scenario: Duplicate account key
- **WHEN** two otherwise valid Account rows have the same canonical account ID
- **THEN** both rows are rejected as duplicate primary keys

#### Scenario: Valid sample data
- **WHEN** all valid sample extracts are standardized with the supplied mapping
- **THEN** all six typed frames are returned and there are zero rejects
