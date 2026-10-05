# Fraud Case – stories and build status

Source: [PRD_Fraud_Case.md](PRD_Fraud_Case.md), section 8, with types from sections 5–6, mapping from section 7, DQ rules from section 10 and decisions from section 11.
Code: [04_code/](04_code/README.md) · Tests: `pytest -q` → 106 passed · Test report: [Test_Report_Fraud_Case.md](Test_Report_Fraud_Case.md)
Decisions: OpenSpec change `openspec/changes/resolve-fraud-case-open-decisions` (Q1–Q7)

| Story | Jira | Status |
|---|---|---|
| FR-01 Ingest case extract | SCRUM-26 | Built |
| FR-02 Standardize data types | SCRUM-27 | Built |
| FR-03 Lifecycle and loss checks | SCRUM-28 | Built; Q6 decided (DQ-10 warns) |
| FR-04 Link to Member 360 | SCRUM-29 | Built; Q1 decided (DQ-14 match-rate gate, off by default) |
| FR-05 Derived case metrics | SCRUM-30 | Built; Q5 decided (SLA by priority, pending Fraud Ops sign-off) |
| FR-06 Publish and govern | SCRUM-31 | Built locally; Q3 (timezone ET), Q4 (DQ-13 optional), Q7 (status snapshot) decided; catalog and access roles are platform tasks |
| FR-07 Account ID mapping reference table | SCRUM-32 | Built; Q2 decided |

## FR-01 Ingest case extract
- [x] 100 rows in raw: `test_ingest.py::test_raw_row_count_matches_file`
- [x] Quoted amounts stay in one column: `test_quoted_amounts_stay_in_one_column`
- [x] Rerun doesn't duplicate rows: `test_rerun_does_not_duplicate_raw_rows`
- [x] Changed header fails fast with the file name: `test_changed_header_fails_fast`
- [x] Load metadata on every row: `test_raw_rows_carry_load_metadata`

## FR-02 Standardize data types
- [x] All 13 columns typed: `test_standardize.py::test_all_13_columns_have_contract_types`, `test_staging_table_declares_contract_types`
- [x] FC0000007 suspected = 1060.33; FC0000002 close = 2026-08-04 16:00: `test_amounts_and_timestamps_parse`
- [x] Bad values / malformed IDs / unknown categories / duplicate IDs → rejects: `test_unparseable_amount_is_rejected`, `test_malformed_member_id_is_rejected`, `test_value_outside_allowed_list_is_rejected`, `test_duplicate_case_ids_are_rejected`
- [x] 0 rejects on the sample: `test_sample_has_no_rejects`

## FR-03 Lifecycle and loss checks
- [x] Sample passes DQ-06..DQ-11: `test_lifecycle.py::test_sample_passes_lifecycle_rules`
- [x] DQ-06 (3 variants), DQ-07, DQ-08 reject with the rule ID: `test_incomplete_lifecycle_is_rejected`, `test_close_before_open_is_rejected`, `test_confirmed_above_suspected_is_rejected`
- [x] DQ-09 warns and keeps the case: `test_false_positive_with_loss_warns_and_keeps_case`
- [x] Q6: DQ-10 warns by default; switchable to reject: `test_confirmed_fraud_without_loss_*`
- [x] DQ-11 rejects cases opened after the run date: `test_cases_opened_after_run_date_are_rejected`

## FR-04 Link to Member 360
- [x] 10 TRUE / 90 FALSE; all kept; 90 MEMBER_NOT_FOUND; DQ-12 Warn: `test_member_link.py`
- [x] Q1: DQ-14 states the match rate (10.00%) and passes by default: `test_match_rate_recorded_without_blocking_by_default`
- [x] Q1: DQ-14 blocks below a minimum and keeps the previous product: `test_match_rate_below_minimum_blocks_and_keeps_previous_product`
- [x] Missing lookup file → clear error: `test_missing_member_reference_fails_clearly`

## FR-05 Derived case metrics
- [x] FC0000002 → 3.00 days, ratio 0.8000; FC0000001 → age 63: `test_metrics.py::test_known_cases`
- [x] NULL rules by lifecycle; sample ranges: `test_metrics_null_by_lifecycle`, `test_sample_metric_ranges`
- [x] Q5: sla_days by priority (30/45/60/90): `test_sla_days_by_priority`
- [x] Q5: sla_breached_flag for open and closed cases: `test_sla_breached_flag`, `test_closed_cases_within_sla`
- [x] Q5: CASE_SLA_BREACHED for open cases = 27 (Critical 15, High 9, Medium 3); CRITICAL_CASE_AGED gone: `test_open_breaches_reported_by_priority`, `test_former_critical_only_exception_is_gone`
- [x] Q5: SLA configurable: `test_sla_days_are_configurable`

## FR-06 Publish and govern
- [x] 100 rows; DQ-01..DQ-05 Pass; all 14 rules recorded: `test_publish.py::test_all_cases_published`, `test_blocking_rules_pass`, `test_every_rule_recorded`
- [x] 23 typed columns in SQLite; CSV starts with the sample's 13 columns, in order: `test_product_table_declares_contract_types`, `test_csv_starts_with_sample_columns`
- [x] Q3: data contract declares America/New_York; values unchanged: `test_contract_declares_eastern_time`
- [x] Q4: DQ-13 off by default (0 rows checked), warns with a matrix: `test_routing.py`
- [x] Q7: daily status snapshot, idempotent per date, success only: `test_status_history.py`
- [x] A blocking failure keeps the previous table; DDL in sync; idempotent rerun: `test_blocking_failure_keeps_previous_product`, `test_committed_ddl_matches_contracts`, `test_rerun_is_idempotent`
- [ ] Catalog entry, access roles, consumer sign-off — platform and people tasks

## FR-07 Account ID mapping reference table (SCRUM-32)
- [x] 110 rows (10 core_banking + 100 fraud_case_mgmt); `A00001` and `A0000001` → `A0000001`: `tools/tests/test_account_id_map.py::test_committed_table_contents`, `test_same_account_across_systems_is_allowed`
- [x] `A0001` / `A00001` / `A0000001` → `A0000001`; `A12345678`, `X1` rejected: `test_any_width_converts_to_canonical`, `test_malformed_ids_are_rejected`
- [x] Collision within a system rejects both rows: `test_collision_within_a_system_rejects_both`
- [x] Committed table is current and valid: `test_committed_table_is_current`, `test_committed_table_is_valid`
- [x] account_found_flag FC0000001 TRUE, FC0000011 FALSE, 90 ACCOUNT_NOT_FOUND: `04_code/tests/test_account_link.py`
