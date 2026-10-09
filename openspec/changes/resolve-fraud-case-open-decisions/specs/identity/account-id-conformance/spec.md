# Spec Delta

## Purpose

Defines the one canonical account ID format shared by all data products, and the account ID mapping reference table that links each source system's account ID to it.

## ADDED Requirements

### Requirement: Canonical account ID format
Every account ID published by a data product SHALL use the canonical format: the letter `A` followed by exactly 7 digits.

#### Scenario: Canonical ID accepted
- **WHEN** a product publishes account ID `A0000001`
- **THEN** the ID is accepted as canonical

#### Scenario: Non-canonical ID refused in published output
- **WHEN** a published account ID does not match `A` + 7 digits (for example `A00001` or `A12`)
- **THEN** the publishing run fails its ID-pattern data quality check for that column

### Requirement: Source account IDs are converted to the canonical format
Any source account ID of the form `A` + 1 to 7 digits SHALL convert to the canonical format by left-padding the number with zeros to 7 digits, whatever its original width.

#### Scenario: Different source widths convert to the same canonical ID
- **WHEN** the source account IDs are `A0001`, `A00001` and `A0000001`
- **THEN** each converts to `A0000001`

#### Scenario: Source ID too long or malformed
- **WHEN** a source account ID has more than 7 digits (`A12345678`) or is not `A` followed by digits (`X1`)
- **THEN** the ID is rejected with a reason and no canonical ID is produced for it

### Requirement: Account ID mapping reference table
An account ID mapping reference table SHALL hold one row per (source system, source account ID), giving the canonical account ID and whether that canonical ID exists in core banking. Products SHALL use this table to link accounts across systems.

#### Scenario: Sample systems are mapped
- **WHEN** the reference table is built from core banking (`A00001`–`A00010`) and fraud case management (`A0000001`–`A0000100`)
- **THEN** it holds 110 rows, and both `core_banking/A00001` and `fraud_case_mgmt/A0000001` map to `A0000001`

#### Scenario: Core banking presence is flagged
- **WHEN** a canonical ID is not among the converted core banking account IDs
- **THEN** its rows have `in_core_banking` FALSE (90 fraud accounts in the sample)

### Requirement: Mapping is one-to-one within a source system
Within one source system, each source account ID SHALL map to exactly one canonical ID, and no two source IDs SHALL share a canonical ID. Across systems, several source IDs MAY map to the same canonical ID.

#### Scenario: Collision within a system is rejected
- **WHEN** one system supplies both `A0001` and `A00001`, which convert to the same canonical ID
- **THEN** both rows are rejected as a mapping collision and neither is published

#### Scenario: Same account across systems is allowed
- **WHEN** `core_banking/A00001` and `fraud_case_mgmt/A0000001` both convert to `A0000001`
- **THEN** both rows are published
