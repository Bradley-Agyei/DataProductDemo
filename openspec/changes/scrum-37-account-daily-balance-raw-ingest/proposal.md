# Proposal

## Why

DP_Account_Daily_Balance (a Jira epic with stories FR-01 to FR-07; SCRUM-37 is FR-01) will publish one governed row per account per calendar day: opening, credits, debits, closing and available balance, and an overdraft flag. Every balance needs to trace back to the source file it came from. FR-01 is the first step: land the core banking extracts unchanged in a raw layer.

## What Changes

- FR-01 goes into the product folder `output/DP_Account_Daily_Balance/04_code/` that SCRUM-43 (FR-07) created on the shared `dp_framework`. Only additions: `config.SOURCE_DIR`/`SOURCE_FILES`; FR-07's `run.py`, `conftest.py` and framework copy are untouched.
- Source contracts for the 6 extracts: Account, Transaction, Transaction_Type, Product, Member and Date.
- A raw layer, built by `raw.py` with its own `python -m src.account_daily_balance.raw` entry point: one `raw_<name>` table per source, untyped text, with `source_file`, `dp_load_ts` and `dp_batch_id` on every row.
- Row counts per file, recorded in `out/raw_manifest.json`.
- A missing file, or a missing or renamed header, fails the run before any table is written.
- Member's `first_name`, `last_name`, `city` and `postal_code` are header-checked but not landed, because CLAUDE.md says PII never leaves `data/raw/`. This is the one deviation from the story's "values unchanged", and it goes one step further than SCRUM-44, which kept the columns with masked values: the attestation review flagged PII-named columns outside `data/raw/` as HIGH. No Account Daily Balance requirement uses those values. PRD §5.5 types all four as PII. The first, second and fourth are found with FR-07's `config.is_pii_column`; `city` is not on that list, so FR-01 adds it itself (`raw.PRD_PII_COLUMNS`).
- `data/raw/` is unchanged.

Out of scope: FR-02 to FR-07 (standardize, balance derivation, checks, publish), which are separate stories. The epic's open questions Q5 (`available_balance` rule) and Q6 (`product_code` source) block later stories, not this one.

## Capabilities

### New Capabilities
- `data-products/account-daily-balance`: raw ingestion for the Account Daily Balance data product.

## Impact

- New: `contracts/sources.py`, `src/account_daily_balance/raw.py`, `tests/test_raw_ingest.py` under `output/DP_Account_Daily_Balance/04_code/`. Updated: `config.py` (additions only), the READMEs and `docs/kt/account-daily-balance/README.md`.
- No change to `DP_Member_360`, `DP_Fraud_Case`, `dp_framework` or FR-07's publish code.
- The Jira story names the source folder `sources/data/raw/`. The repo uses `data/raw/`.
- The PRD (`output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md`, Draft v0.1) is on `develop`. FR-01 (§8) and the source inventory (§5) match this change. This change has no `prd.md` of its own, so spec-gate reports it as NOT TRACED.
- The epic's target schema uses `member_id` only, so no later story needs the Member name or postal code columns.
