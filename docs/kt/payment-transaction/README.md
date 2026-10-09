# Payment Transaction data product: knowledge transfer

## What this is

`DP_Payment_Transaction` (Jira epic SCRUM-36) will publish one governed row per payment transaction. It's being built story by story, and only **FR-01, raw ingestion (SCRUM-44)**, exists so far. It is the third product on `dp_framework`, after `DP_Member_360` and `DP_Fraud_Case`.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Payment_Transaction/04_code/` | Contracts, pipeline and tests | `04_code/README.md` |
| `output/DP_Payment_Transaction/PRD_Payment_Transaction.md` | PRD: target schema, mapping, FR-01 to FR-07, DQ rules, open questions | sections 6, 8 and 10 |
| `openspec/changes/scrum-44-payment-transaction-raw-ingest/` | FR-01 requirements and scenarios | `proposal.md` |
| Jira SCRUM-45 to SCRUM-50 | FR-02 to FR-07, not built yet | the stories |

## How FR-01 works

1. `dp_framework.ingest.ingest_all` reads the 7 extracts from `data/raw/` as text and checks each header against `contracts/sources.py`. If anything is wrong, it raises `SchemaError` naming the file, before anything is written.
2. `raw.py` renames the framework's `src_file_name` and `src_load_ts` columns to `source_file` and `dp_load_ts`, the names FR-01 specifies. It does not edit the framework instead, because every product's copy must stay byte-identical.
3. Every PII value is replaced with `*`, in memory, before anything is written.
4. Each source lands as a `raw_<name>` TEXT table in `payment_transaction.db`. The row counts go to `out/raw_manifest.json`.

## Things to know

- **PII is masked.** FR-01 says to land Member unchanged, but CLAUDE.md says PII never leaves `data/raw/`, and the attestation review flagged the full copy as HIGH. So Member's `first_name`, `last_name`, `city` and `postal_code` (the PII columns in PRD §5.7) keep their columns, but every value is replaced with `*`. Branch's `city` and `postal_code` are masked too, because PRD §5.5 hides them as matching member PII (`config.PII_MASKED_COLUMNS`). No later story needs them. If one ever does, it needs a decision, not a config change.
- **Path difference.** The Jira stories say `sources/data/raw/`. The repo uses `data/raw/`.
- **PRD.** `output/DP_Payment_Transaction/PRD_Payment_Transaction.md` (Draft v0.1) defines the 20-column target, the source-to-target mapping, FR-01 to FR-07, DQ-01 to DQ-14 and open questions Q1 to Q11. Things to know when reading it against the code:
  - **Paths.** The PRD writes `sources/data/raw/` and `data/output/product/`. The repo uses `data/raw/` and `data/product/`.
  - **PII.** FR-01 says to land the extracts unchanged, but §4 and §9 rule out PII. The raw layer masks Member `first_name`, `last_name`, `city` and `postal_code`, and Branch `city` and `postal_code`, with `*`.
  - **Not traced yet.** The OpenSpec change `scrum-44-payment-transaction-raw-ingest` still has no `prd.md`, so spec-gate reports it as NOT TRACED. Tracing FR-01 needs a `prd.md` in that change plus `# implements:` markers in the code.
- **Source contracts are pinned to the PRD.** `contracts/sources.py` started as a copy of Member 360's contracts. It now follows PRD §5. `tests/test_source_contract.py` reads the §5 tables from the PRD file, so a PRD edit that the contract doesn't follow fails the build.
- **Raw data baseline (2026-10-08).** The 7 extracts match the PRD:
  - every primary key unique;
  - every ID in its §5 raw format;
  - 0 orphan foreign keys;
  - the member and branch match the account on 100 of 100 transactions;
  - the direction matches the type on 100 of 100 transactions;
  - all 10 accounts present in `account_id_map`;
  - `date_key` agrees with `full_date` on all 10 days.

  The same test file re-checks this. If it fails on a new extract, report it to the source owner. Don't edit `data/raw/`.
