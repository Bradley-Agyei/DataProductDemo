# Tasks

## 1. Product scaffold

- [x] 1.1 Create `output/DP_Account_Daily_Balance/04_code/` with `pytest.ini`, `requirements.txt` and `.gitignore` matching the other products. Copy `src/dp_framework/` unchanged. Verify: `tests/test_framework_sync.py` passes.
- [x] 1.2 Add `contracts/account_daily_balance.py` (15 columns from the epic's target schema, key `balance_date` + `account_id`, `product_code` and `available_balance` pending) and `DQ_EXCEPTIONS`. Verify: `test_product_table_declares_contract_types`, `test_data_contract`.

## 2. FR-07 publish (SCRUM-43)

- [x] 2.1 Add `dq_rules.py` with DQ-01 to 07 and DQ-10 (block) and DQ-11 (warn). Verify: `test_critical_rules_pass_on_clean_input`, `test_critical_failure_blocks_and_keeps_previous_product` for each critical rule, and `test_dq07_catches_offsetting_credit_and_debit_errors`.
- [x] 2.2 Add `exceptions.py`, which reports upstream rejects and warnings with their rule IDs. Verify: `test_exception_report_lists_rejects_and_warnings_with_rule_id`.
- [x] 2.3 Add `pii.py`, which masks PII-named columns and PII reject values with `*`. Verify: `test_pii_column_reaching_publish_is_masked_and_never_written`, `test_pii_reject_value_and_reason_are_masked`, `test_contract_has_no_pii_columns`.
- [x] 2.4 Add `run.py` with `publish()`, which writes the ops tables on every run and the product, CSV and contract only on SUCCESS, plus `--write-ddl`. Verify: `test_csv_header_starts_with_sample_columns`, `test_blocked_first_run_publishes_nothing`, `test_rerun_is_idempotent`, `test_run_log_written`, `test_committed_ddl_matches_contracts`.

## 3. Docs

- [x] 3.1 Add `PRD_Account_Daily_Balance.md` (Draft v0.1) and check the contract and DQ rules against PRD §6 and §10.
- [x] 3.2 Add `04_code/README.md`, `docs/kt/account-daily-balance/README.md` and a row in `output/README.md`.
