# Account Daily Balance data product: knowledge transfer

## What this is

`DP_Account_Daily_Balance` (Jira epic SCRUM-35) will publish one governed row per account per calendar day: opening, credits, debits, closing, available balance and overdraft flag. Its users are Finance & reporting and Fraud & risk. It's the fourth product on `dp_framework`.

Two steps exist so far: **FR-01, raw ingestion (SCRUM-37)**, the first step, and **FR-07, publish (SCRUM-43)**, the last. Publish was built first so that the gate, the contract and the outputs are fixed before the steps that feed them.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md` | PRD: target schema, mapping, FR-01 to FR-07, DQ rules, open questions | sections 6, 8 and 10 |
| `output/DP_Account_Daily_Balance/04_code/` | Contract, publish step, DQ rules and tests | `04_code/README.md` |
| `openspec/changes/scrum-37-account-daily-balance-raw-ingest/` | FR-01 requirements and scenarios | `proposal.md` |
| `openspec/changes/scrum-43-account-daily-balance-publish/` | FR-07 requirements and scenarios | `proposal.md` |
| Jira SCRUM-38 to SCRUM-42 | FR-02 to FR-06: standardize, totals, roll-forward, overdraft, attributes | the stories |

## How raw ingestion works

`build()` in `src/account_daily_balance/raw.py`, run with `python -m src.account_daily_balance.raw`:

1. **Header gate.** Every file is read and its header checked before anything is written, so a renamed or missing column (or missing file) fails the run with nothing published.
2. **PII drop.** Member `first_name`, `last_name`, `city` and `postal_code` are header-checked but not landed. This is the one place the story's "values unchanged" does not hold: CLAUDE.md forbids PII outside `data/raw/`, and the attestation review flags even masked PII-named columns as HIGH. The column set is FR-07's `is_pii_column` plus `city`, which PRD §5.5 types as PII but the repo-wide list lacks. SCRUM-44 kept its PII columns with masked values; this goes further.
3. **Write.** One `raw_<name>` table per file, all text, plus `source_file`, `dp_load_ts` and `dp_batch_id`. `out/raw_manifest.json` holds row counts and a count of PII columns dropped, never a name or value.

The sources live in `data/raw/`. The story and the PRD say `sources/data/raw/`, which doesn't exist. `account_id_map` is listed as a PRD source but FR-01 doesn't load it.

## How publishing works

`publish(product, counted_transactions, upstream_rejects)` in `src/account_daily_balance/run.py`:

1. **PII guard.** Any PII-named column is masked with `*`, and so is the raw value of a reject on a PII column.
2. **DQ gate.** DQ-01 to 07 and DQ-10 block publishing. DQ-11 only warns.
3. **Exception report.** Upstream rejects and the warnings are listed with their rule IDs.
4. **Write.**
   - Always written: the ops tables (rejects, DQ results, run log) and the exception report.
   - Written only on SUCCESS: the product table, the CSV and the data contract. That's why a blocked run leaves the previous product in place.

`counted_transactions` must hold one row per counted transaction, with `account_id` and `signed_amount` (credit positive, debit negative). FR-03 produces it, and DQ-07 reconciles against it.

## Things to know

- **PRD.** `PRD_Account_Daily_Balance.md` (Draft v0.1) is the spec. The contract follows §6, and the DQ rules follow §10. DQ-07 reconciles credits and debits separately. Things to know when reading it against the code:
  - **Paths.** The PRD writes `sources/data/raw/` and `data/output/product/`. The repo uses `data/raw/` and `data/product/`.
  - **No sample yet.** The target sample is shape only (Q1) and isn't committed, so the header test uses the first 11 columns in §6.
  - **Not traced yet.** The OpenSpec change has no `prd.md`, so spec-gate doesn't trace the ACs.
- **Pending columns.** `product_code` (Q6) and `available_balance` (Q5) are `pending`, so they're published as NULL until their stories are unblocked.
- **No end-to-end run yet.** The story's verify step (sample run, 100 rows) needs FR-01 to FR-06. Until then, publishing is tested on a 2-account, 3-day fixture in `tests/conftest.py`.
