# Spec Delta

## Purpose

Defines how the Account Daily Balance data product lands its core banking extracts in the raw layer.

## ADDED Requirements

### Requirement: Source extracts land unchanged as text
The run SHALL land each of the 6 source extracts (Account, Transaction, Transaction_Type, Product, Member, Date) in its own raw table, with every source value kept exactly as received, as untyped text, except PII columns, which are not landed.

#### Scenario: Values are not coerced
- **WHEN** the run loads the sample extracts
- **THEN** each raw table's source columns are equal to the file read as text, and every source column has type TEXT

### Requirement: Row counts are recorded per file
The run SHALL record the number of rows landed from each source file.

#### Scenario: Sample row counts
- **WHEN** the run loads the sample extracts
- **THEN** the recorded counts are Account 10, Transaction 100 and 10 for each of the other four files

### Requirement: A header change fails the run before publish
The run SHALL check every source header against its contract before writing anything. A missing file, a missing column or a renamed column SHALL fail the run, and no raw table or manifest SHALL be written.

#### Scenario: Renamed column
- **WHEN** `product_name` in Product.csv is renamed
- **THEN** the run fails with an error naming Product.csv and no output is written

#### Scenario: Missing column
- **WHEN** the last column of Product.csv is removed
- **THEN** the run fails with an error naming Product.csv and no output is written

#### Scenario: Missing file
- **WHEN** Date.csv is absent
- **THEN** the run fails with an error naming Date.csv and no output is written

### Requirement: Every raw row carries load metadata
Every raw row SHALL carry `source_file` (VARCHAR(255)), `dp_load_ts` (TIMESTAMP) and `dp_batch_id` (VARCHAR(36)). `dp_batch_id` SHALL be the same for every row of a run and SHALL default to a UUID.

#### Scenario: Load columns on each row
- **WHEN** the run loads the sample extracts with a given batch ID and load time
- **THEN** every row of every raw table has its own file name, that load time and that batch ID

### Requirement: PII never leaves data/raw
The run SHALL drop Member's `first_name`, `last_name`, `city` and `postal_code` before anything is written, so no PII name or value reaches the raw layer. Their headers SHALL still be checked, so renaming or removing one fails the run. The row count record SHALL contain counts only, never row values or PII column names.

#### Scenario: PII columns are not landed
- **WHEN** the run loads the sample extracts
- **THEN** `raw_member` has no `first_name`, `last_name`, `city` or `postal_code` column, still has 10 rows, and the manifest records only that 4 PII columns were dropped

#### Scenario: Renamed PII column
- **WHEN** `first_name` in Member.csv is renamed
- **THEN** the run fails with an error naming Member.csv and no output is written

#### Scenario: Manifest holds no values
- **WHEN** the run completes
- **THEN** `raw_manifest.json` contains the batch ID, the load time, one row count per file and the number of PII columns dropped per file, and nothing else
