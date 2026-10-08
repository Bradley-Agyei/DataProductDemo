# Payment Transaction data product: knowledge transfer

## What this is

`DP_Payment_Transaction` (Jira epic SCRUM-36) will publish one governed row per payment transaction. It's being built story by story, and only **FR-01, raw ingestion (SCRUM-44)**, exists so far. It is the third product on `dp_framework`, after `DP_Member_360` and `DP_Fraud_Case`.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Payment_Transaction/04_code/` | Contracts, pipeline and tests | `04_code/README.md` |
| `openspec/changes/scrum-44-payment-transaction-raw-ingest/` | FR-01 requirements and scenarios | `proposal.md` |
| Jira SCRUM-45 to SCRUM-50 | FR-02 to FR-07, not built yet | the stories |

## How FR-01 works

1. `dp_framework.ingest.ingest_all` reads the 7 extracts from `data/raw/` as text and checks each header against `contracts/sources.py`. If anything is wrong, it raises `SchemaError` naming the file, before anything is written.
2. `raw.py` renames the framework's `src_file_name` and `src_load_ts` columns to `source_file` and `dp_load_ts`, the names FR-01 specifies. It does not edit the framework instead, because every product's copy must stay byte-identical.
3. Every PII value is replaced with `*`, in memory, before anything is written.
4. Each source lands as a `raw_<name>` TEXT table in `payment_transaction.db`. The row counts go to `out/raw_manifest.json`.

## Things to know

- **PII is masked.** FR-01 says to land Member unchanged, but CLAUDE.md says PII never leaves `data/raw/`, and the attestation review flagged the full copy as HIGH. So Member's `first_name`, `last_name` and `postal_code` keep their columns, but every value is replaced with `*`. Branch's `postal_code` is masked too, because the pii gate treats every `postal_code` as PII (`config.PII_MASKED_COLUMNS`). No later story needs them. If one ever does, it needs a decision, not a config change.
- **Path difference.** The Jira stories say `sources/data/raw/`. The repo uses `data/raw/`.
- **No PRD in the repo for this product.** The Jira story is the spec, so the OpenSpec change has no `prd.md` and spec-gate reports it as NOT TRACED. Add the PRD there when it exists.
