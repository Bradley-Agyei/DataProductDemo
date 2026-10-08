# DP_Payment_Transaction: code

Payment Transaction data product (Jira epic SCRUM-36). Built on the shared `dp_framework`, the same as `DP_Member_360` and `DP_Fraud_Case`.

Only FR-01 is built so far, under SCRUM-44. The requirements are in the PRD, `../PRD_Payment_Transaction.md`.

## FR-01 Ingest transaction extracts (SCRUM-44)

- **Sources:** Transaction, Transaction_Type, Channel, Date, Branch, Account and Member. They're read from `data/raw/`, which is read-only. The story calls this folder `sources/data/raw/`.
- **Header check:** `dp_framework.ingest` reads every file as text and checks its header against `contracts/sources.py`. A missing file, or a missing or renamed column, raises `SchemaError` before any table is written.
- **Raw tables:** each source becomes a `raw_<name>` table, untyped `TEXT`, in `payment_transaction.db`. Each row gets `source_file`, `dp_load_ts` and `dp_batch_id`.
  - The framework names the first two `src_file_name` and `src_load_ts`. `src/payment_transaction/raw.py` renames them to the FR-01 names, so the framework stays byte-identical across products.
- **Row counts:** written to `out/raw_manifest.json`, which holds counts only.

**PII:** Member's `first_name`, `last_name` and `postal_code`, and Branch's `postal_code`, are header-checked and landed with every value replaced by `*` (`config.PII_MASKED_COLUMNS`). The manifest lists them as masked. The `.db` file and `out/` are git-ignored anyway.

## Run
```bash
pip install -r requirements.txt
pytest -q
python -m src.payment_transaction.run
```

## Layout
| Path | What |
|---|---|
| `contracts/sources.py` | One `Column` per column of the 7 source CSVs |
| `src/dp_framework/` | Shared framework, a byte-identical copy (checked by `tests/test_framework_sync.py`) |
| `src/payment_transaction/raw.py` | FR-01: rename load columns, land raw tables, record row counts |
| `src/payment_transaction/run.py` | Pipeline entry point |
| `tests/test_raw_ingest.py` | One test per FR-01 acceptance criterion |
