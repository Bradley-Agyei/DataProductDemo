# Tasks

## 1. Contracts

- [x] 1.1 Add `contracts/sources.py` with the 6 source tables (columns as in the Member 360 source contracts). The product scaffold and `dp_framework` copy already came in with SCRUM-43. Verify: `test_six_sources_in_scope`, `tests/test_framework_sync.py`.

## 2. FR-01 raw ingestion (SCRUM-37)

- [x] 2.1 Add `src/account_daily_balance/raw.py`: ingest through `dp_framework.ingest.ingest_all`, rename the load columns to `source_file`/`dp_load_ts`, land `raw_<name>` TEXT tables, and write a counts-only `raw_manifest.json`. Verify: `test_values_land_unchanged_as_text`, `test_raw_columns_are_untyped_text`, `test_row_counts_recorded`, `test_rows_carry_load_columns`.
- [x] 2.2 Add the header gate behaviour checks (renamed column, missing column, missing file → nothing written). Verify: `test_header_change_fails_before_anything_is_written`, `test_missing_file_fails_before_anything_is_written`.
- [x] 2.3 Add `build()` and a CLI to `raw.py`, and `SOURCE_DIR`/`SOURCE_FILES` to `config.py`. FR-07's `run.py` and `tests/conftest.py` are left as they are. Verify: `python -m src.account_daily_balance.raw` prints Account 10, Transaction 100 and 10 for each of the other four files.
- [x] 2.4 Drop Member `first_name`, `last_name`, `city` and `postal_code` after the header check (`raw.pii_columns`: FR-07's `config.is_pii_column` plus the PRD's `city`). Verify: `test_pii_columns_are_not_landed`, `test_renamed_pii_column_still_fails_the_header_check`.

## 3. Docs

- [x] 3.1 Add an FR-01 section to `04_code/README.md` and `docs/kt/account-daily-balance/README.md`, and update the row in `output/README.md`.
