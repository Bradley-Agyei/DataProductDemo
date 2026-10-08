# Proposal

## Why

DP_Payment_Transaction (Jira epic SCRUM-36) needs every published transaction row to trace back to the source file it came from. FR-01 (Jira SCRUM-44, PRD §8 FR-01) is the first step: land the transaction extract and its reference tables unchanged in a raw layer.

## What Changes

- A new product folder, `output/DP_Payment_Transaction/04_code/`, on the shared `dp_framework`. Its copy of the framework is byte-identical to the other products' copies.
- Source contracts for the 7 extracts: Transaction, Transaction_Type, Channel, Date, Branch, Account and Member.
- A raw layer: one `raw_<name>` table per source, untyped text, with `source_file`, `dp_load_ts` and `dp_batch_id` on every row.
- Row counts per file, recorded in `out/raw_manifest.json`.
- A missing file, or a missing or renamed header, fails the run before any table is written.
- `data/raw/` is unchanged. The raw layer holds Member PII exactly as received, so it's written only to git-ignored paths.

Out of scope: FR-02 to FR-07 (standardize, enrich, integrity checks, risk signals, publish), which are SCRUM-45 to SCRUM-50.

## Capabilities

### New Capabilities
- `data-products/payment-transaction`: raw ingestion for the Payment Transaction data product.

## Impact

- New: `output/DP_Payment_Transaction/04_code/`, `docs/kt/payment-transaction/README.md`.
- No change to `DP_Member_360`, `DP_Fraud_Case` or `dp_framework`.
