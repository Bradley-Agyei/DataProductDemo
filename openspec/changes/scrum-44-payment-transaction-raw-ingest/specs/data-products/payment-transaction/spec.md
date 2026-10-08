# Spec Delta

## Purpose

Defines how the Payment Transaction data product lands its source extracts in the raw layer.

## ADDED Requirements

### Requirement: Source extracts land unchanged as text
The run SHALL land each of the 7 source extracts (Transaction, Transaction_Type, Channel, Date, Branch, Account, Member) in its own raw table, with every source value kept exactly as received, as untyped text.

#### Scenario: Values are not coerced
- **WHEN** the run loads the sample extracts
- **THEN** each raw table's source columns are equal to the file read as text, and every source column has type TEXT

### Requirement: Row counts are recorded per file
The run SHALL record the number of rows landed from each source file.

#### Scenario: Sample row counts
- **WHEN** the run loads the sample extracts
- **THEN** the recorded counts are Transaction 100 and 10 for each of the other six files

### Requirement: A header change fails the run before publish
The run SHALL check every source header against its contract before writing anything. A missing file, a missing column or a renamed column SHALL fail the run, and no raw table or manifest SHALL be written.

#### Scenario: Renamed column
- **WHEN** `channel_name` in Channel.csv is renamed
- **THEN** the run fails with an error naming Channel.csv and no output is written

#### Scenario: Missing column
- **WHEN** the last column of Channel.csv is removed
- **THEN** the run fails with an error naming Channel.csv and no output is written

#### Scenario: Missing file
- **WHEN** Branch.csv is absent
- **THEN** the run fails with an error naming Branch.csv and no output is written

### Requirement: Every raw row carries load metadata
Every raw row SHALL carry `source_file` (VARCHAR(255)), `dp_load_ts` (TIMESTAMP) and `dp_batch_id` (VARCHAR(36)). `dp_batch_id` SHALL be the same for every row of a run and SHALL default to a UUID.

#### Scenario: Load columns on each row
- **WHEN** the run loads the sample extracts with a given batch ID and load time
- **THEN** every row of every raw table has its own file name, that load time and that batch ID

### Requirement: Raw PII stays out of version control
The raw layer SHALL be written only to git-ignored paths. The row count record SHALL contain counts only, never row values.

#### Scenario: Manifest holds counts only
- **WHEN** the run completes
- **THEN** `raw_manifest.json` contains the batch ID, the load time and one row count per file, and nothing else
