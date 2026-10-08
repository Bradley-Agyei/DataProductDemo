# Tasks

## 1. Product scaffold

- [x] 1.1 Create `output/DP_Payment_Transaction/04_code/` with `pytest.ini`, `requirements.txt` and `.gitignore` matching the other products. Copy `src/dp_framework/` unchanged. Verify: `tests/test_framework_sync.py` passes.
- [x] 1.2 Add `contracts/sources.py` with the 7 source tables (columns as in the Member 360 source contracts). Verify: `test_seven_sources_in_scope`.

## 2. FR-01 raw ingestion (SCRUM-44)

- [x] 2.1 Add `src/payment_transaction/raw.py`: ingest through `dp_framework.ingest.ingest_all`, rename the load columns to `source_file`/`dp_load_ts`, land `raw_<name>` TEXT tables, and write a counts-only `raw_manifest.json`. Verify: `test_values_land_unchanged_as_text`, `test_raw_columns_are_untyped_text`, `test_row_counts_recorded`, `test_rows_carry_load_columns`.
- [x] 2.2 Add the header gate behaviour checks (renamed column, missing column, missing file → nothing written). Verify: `test_header_change_fails_before_anything_is_written`, `test_missing_file_fails_before_anything_is_written`.
- [x] 2.3 Add `src/payment_transaction/run.py` with the CLI. Verify: `python -m src.payment_transaction.run` prints Transaction 100 rows and 10 for each of the other six files.

## 3. Docs

- [x] 3.1 Add `04_code/README.md`, `docs/kt/payment-transaction/README.md` and a row in `output/README.md`.
