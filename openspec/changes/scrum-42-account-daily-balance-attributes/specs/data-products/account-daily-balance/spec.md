# Spec Delta

## Purpose

Defines the Account Daily Balance data product: one governed balance row per account per calendar day, with the account attributes and data-quality warnings analysts rely on.

## ADDED Requirements

### Requirement: Each balance row carries the account's current status
Every product row SHALL carry the `account_status` of its account as held in the Account source on the run date, the same value on every day for that account. Values outside Open and Restricted SHALL fail DQ-04 and block the run.

#### Scenario: Restricted account
- **WHEN** an account's source status is Restricted
- **THEN** every product row for that account has `account_status` Restricted

#### Scenario: Unknown status blocks
- **WHEN** an account's source status is Closed
- **THEN** DQ-04 fails and the run is BLOCKED

### Requirement: Each balance row carries the account's member
Every product row SHALL carry the conformed `member_id` of its account's owner from the Account source.

#### Scenario: Member ID conformed
- **WHEN** the Account source gives member `M0004` for an account
- **THEN** every product row for that account has `member_id` M000004

### Requirement: Product code comes from the product code reference table
`product_code` SHALL be looked up from the product code reference table by the account's `product_id`. No product code SHALL be derived from hard-coded values in the pipeline.

#### Scenario: Reference table maps the product
- **WHEN** the reference table maps P001 to CHK_STD and an account has product P001
- **THEN** every product row for that account has `product_code` CHK_STD

#### Scenario: Mapping changes with the table, not the code
- **WHEN** the reference table maps P001 to CHK_REW instead
- **THEN** the same run publishes `product_code` CHK_REW for that account with no code change

### Requirement: Product code stays pending until the reference table is supplied
While no product code reference table is supplied, the run SHALL publish `product_code` as NULL, SHALL NOT be blocked for it, and the data contract SHALL keep `product_code` marked pending.

#### Scenario: No reference table
- **WHEN** a run has no product code reference table
- **THEN** the run is not blocked by product_code, every `product_code` is NULL, and the data contract lists `product_code` as pending

### Requirement: An invalid reference table stops the run
A supplied product code reference table SHALL be rejected, and the run SHALL stop before publishing anything, when the table has a duplicate `product_id`, a missing `product_id` or `product_code`, or a code outside the DQ-04 allowed product codes.

#### Scenario: Duplicate product_id
- **WHEN** the reference table lists P001 twice
- **THEN** the run stops with an error naming the duplicate and publishes nothing

#### Scenario: Code not allowed
- **WHEN** the reference table maps P011 to CHK_GOLD
- **THEN** the run stops with an error naming the code and publishes nothing

### Requirement: Unmatched products are warned, not blocked
When a reference table is supplied and an account's `product_id` is missing or has no match in it, that account's `product_code` SHALL be NULL and the exception report SHALL carry one DQ-14 warning for the account. The run SHALL NOT be blocked by this.

#### Scenario: Product not in the table
- **WHEN** the reference table has no row for an account's product P010
- **THEN** that account's rows have NULL `product_code`, the exception report has one WARN row with rule DQ-14 keyed by the account, and the run publishes

### Requirement: Dormant members with activity are reported once per run
The exception report SHALL contain one DQ-13 warning for each member whose status is Dormant and who has at least one source transaction of any status in the run, keyed by `member_id`. The rule SHALL be based on member status, not on account status or fixed member IDs. A DQ-13 warning SHALL NOT block the run.

#### Scenario: Dormant member with Pending transactions only
- **WHEN** a Dormant member's only account has Pending transactions and no Posted transactions
- **THEN** the exception report has one WARN row with rule DQ-13 and row key equal to that member's ID

#### Scenario: Dormant member with an Open account
- **WHEN** a Dormant member's account is Open and has transactions
- **THEN** the member is reported under DQ-13

#### Scenario: Restricted account of an Active member
- **WHEN** an Active member's account is Restricted and has transactions
- **THEN** no DQ-13 warning is raised for that member

#### Scenario: Dormant member without activity
- **WHEN** a Dormant member has no source transactions in the run
- **THEN** no DQ-13 warning is raised for that member

#### Scenario: Several accounts, several days
- **WHEN** a Dormant member has transactions on two accounts across three days
- **THEN** exactly one DQ-13 warning is raised for that member

#### Scenario: Sample sources
- **WHEN** the run uses the sample sources in `data/raw/`
- **THEN** the exception report has DQ-13 warnings for exactly M000004 and M000008

### Requirement: Attribute warnings carry no member PII
DQ-13 and DQ-14 warning details SHALL contain only IDs, rule descriptions and counts. They SHALL NOT contain member names, postal codes or any other Member PII.

#### Scenario: Dormant warning detail
- **WHEN** a DQ-13 warning is written
- **THEN** its detail states the rule and the transaction and account counts, and contains no value from a Member PII column
