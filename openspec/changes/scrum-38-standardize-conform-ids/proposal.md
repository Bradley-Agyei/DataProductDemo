# Proposal

## Why

DP_Account_Daily_Balance needs typed source frames and canonical account/member
identifiers before transaction totals and the balance roll-forward can operate
on the data. SCRUM-38 implements FR-02 after FR-01's raw ingestion.

## What Changes

- Add source contracts for the six extracts, limited to fields retained by the
  raw-layer PII controls.
- Add a standardization step that parses source values to their PRD §5 types,
  maps core banking account IDs using `data/reference/account_id_map.csv`,
  and left-pads member identifiers.
- Return row-level rejects for parse errors, duplicate keys, and unmapped
  account IDs; unmapped account IDs use reason `DQ-08`.
- Add sample and unit tests for all FR-02 conversions.

## Out of Scope

- Raw ingestion (FR-01), transaction counting (FR-03), and the balance
  roll-forward (FR-04).
- Modifications to upstream source files or the SCRUM-37 branch.
