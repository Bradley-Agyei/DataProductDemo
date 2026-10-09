# Unit Test Cases – DP_Fraud_Case

- **Generated:** 2026-10-05 by `python -m tools.build_unit_test_cases`, from a real pytest run
- **Result:** 127 / 127 passed
- **Type:** automated pytest. Story-level tests run the pipeline on the real sample sources; Framework tests cover shared building blocks in isolation.

## Summary by story

| Story | Jira | Test cases | Passed |
|---|---|---|---|
| FR-01 Ingest case extract | SCRUM-26 | 5 | 5 |
| FR-02 Standardize data types | SCRUM-27 | 33 | 33 |
| FR-03 Lifecycle and loss checks | SCRUM-28 | 15 | 15 |
| FR-04 Link to Member 360 | SCRUM-29 | 6 | 6 |
| FR-05 Derived case metrics | SCRUM-30 | 12 | 12 |
| FR-06 Publish and govern | SCRUM-31 | 16 | 16 |
| FR-06 Publish and govern (routing check) | SCRUM-31 | 3 | 3 |
| FR-06 Publish and govern (status history) | SCRUM-31 | 4 | 4 |
| FR-07 Account ID mapping | SCRUM-32 | 4 | 4 |
| Shared: account ID mapping reference table | SCRUM-32 | 21 | 21 |
| Framework | - | 8 | 8 |

## Test cases

| TC ID | Story | Jira | Test file | Test case | Description / expected result | Result | Time (s) |
|---|---|---|---|---|---|---|---|
| UT-FC-001 | FR-01 Ingest case extract | SCRUM-26 | tests/test_ingest.py | test_raw_row_count_matches_file | Raw row count matches file | Pass | 0.006 |
| UT-FC-002 | FR-01 Ingest case extract | SCRUM-26 | tests/test_ingest.py | test_raw_rows_carry_load_metadata | Raw rows carry load metadata | Pass | 0.002 |
| UT-FC-003 | FR-01 Ingest case extract | SCRUM-26 | tests/test_ingest.py | test_quoted_amounts_stay_in_one_column | Quoted amounts stay in one column | Pass | 0.002 |
| UT-FC-004 | FR-01 Ingest case extract | SCRUM-26 | tests/test_ingest.py | test_rerun_does_not_duplicate_raw_rows | Rerun does not duplicate raw rows | Pass | 0.226 |
| UT-FC-005 | FR-01 Ingest case extract | SCRUM-26 | tests/test_ingest.py | test_changed_header_fails_fast | Changed header fails fast | Pass | 0.08 |
| UT-FC-006 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_all_13_columns_have_contract_types | All 13 columns have contract types | Pass | 0.001 |
| UT-FC-007 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_staging_table_declares_contract_types | Staging table declares contract types | Pass | 0.002 |
| UT-FC-008 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_amounts_and_timestamps_parse | Amounts and timestamps parse | Pass | 0.001 |
| UT-FC-009 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_blanks_become_null_only_where_allowed | Blanks become null only where allowed | Pass | 0.001 |
| UT-FC-010 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_sample_has_no_rejects | Sample has no rejects | Pass | 0.001 |
| UT-FC-011 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_unparseable_amount_is_rejected | Unparseable amount is rejected | Pass | 0.187 |
| UT-FC-012 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_malformed_member_id_is_rejected | Malformed member id is rejected | Pass | 0.192 |
| UT-FC-013 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_value_outside_allowed_list_is_rejected | Value outside allowed list is rejected | Pass | 0.202 |
| UT-FC-014 | FR-02 Standardize data types | SCRUM-27 | tests/test_standardize.py | test_duplicate_case_ids_are_rejected | Duplicate case ids are rejected | Pass | 0.168 |
| UT-FC-015 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_currency_text_becomes_decimal[$500.00 -expected0] | Currency text becomes decimal [$500.00 -expected0] | Pass | 0.002 |
| UT-FC-016 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_currency_text_becomes_decimal[$1,225.35 -expected1] | Currency text becomes decimal [$1,225.35 -expected1] | Pass | 0.001 |
| UT-FC-017 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_currency_text_becomes_decimal[($199.78)-expected2] | Currency text becomes decimal [($199.78)-expected2] | Pass | 0.001 |
| UT-FC-018 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_currency_text_becomes_decimal[-12.5-expected3] | Currency text becomes decimal [-12.5-expected3] | Pass | 0.001 |
| UT-FC-019 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_currency_text_becomes_decimal[0-expected4] | Currency text becomes decimal [0-expected4] | Pass | 0.001 |
| UT-FC-020 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_non_numeric_currency_is_rejected | Non numeric currency is rejected | Pass | 0.001 |
| UT-FC-021 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_decimal_precision_is_enforced | Decimal precision is enforced | Pass | 0.001 |
| UT-FC-022 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[DATE-1/8/2019-expected0] | Parse value by type [DATE-1/8/2019-expected0] | Pass | 0.001 |
| UT-FC-023 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[DATE-2019-01-08-expected1] | Parse value by type [DATE-2019-01-08-expected1] | Pass | 0.002 |
| UT-FC-024 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[TIMESTAMP-9/2/2026 9:01-expected2] | Parse value by type [TIMESTAMP-9/2/2026 9:01-expected2] | Pass | 0.002 |
| UT-FC-025 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[BOOLEAN-TRUE-True] | Parse value by type [BOOLEAN-TRUE-True] | Pass | 0.001 |
| UT-FC-026 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[BOOLEAN-false-False] | Parse value by type [BOOLEAN-false-False] | Pass | 0.001 |
| UT-FC-027 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[INT-20260921-20260921] | Parse value by type [INT-20260921-20260921] | Pass | 0.001 |
| UT-FC-028 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[SMALLINT-2026-2026] | Parse value by type [SMALLINT-2026-2026] | Pass | 0.001 |
| UT-FC-029 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[CHAR(5)-12345-12345] | Parse value by type [CHAR(5)-12345-12345] | Pass | 0.001 |
| UT-FC-030 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_parse_value_by_type[VARCHAR(10)- A00001 -A00001] | Parse value by type [VARCHAR(10)- A00001 -A00001] | Pass | 0.001 |
| UT-FC-031 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_invalid_values_raise[BOOLEAN-maybe] | Invalid values raise [BOOLEAN-maybe] | Pass | 0.001 |
| UT-FC-032 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_invalid_values_raise[DATE-31/31/2020] | Invalid values raise [DATE-31/31/2020] | Pass | 0.001 |
| UT-FC-033 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_invalid_values_raise[INT-12.5] | Invalid values raise [INT-12.5] | Pass | 0.001 |
| UT-FC-034 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_invalid_values_raise[SMALLINT-70000] | Invalid values raise [SMALLINT-70000] | Pass | 0.001 |
| UT-FC-035 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_invalid_values_raise[CHAR(2)-NCX] | Invalid values raise [CHAR(2)-NCX] | Pass | 0.001 |
| UT-FC-036 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_invalid_values_raise[VARCHAR(3)-ABCD] | Invalid values raise [VARCHAR(3)-ABCD] | Pass | 0.001 |
| UT-FC-037 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_blank_is_null | Blank is null | Pass | 0.001 |
| UT-FC-038 | FR-02 Standardize data types | SCRUM-27 | tests/test_types.py | test_postal_code_keeps_leading_zero | Postal code keeps leading zero | Pass | 0.001 |
| UT-FC-039 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_sample_passes_lifecycle_rules[DQ-06] | Sample passes lifecycle rules [DQ-06] | Pass | 0.002 |
| UT-FC-040 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_sample_passes_lifecycle_rules[DQ-07] | Sample passes lifecycle rules [DQ-07] | Pass | 0.002 |
| UT-FC-041 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_sample_passes_lifecycle_rules[DQ-08] | Sample passes lifecycle rules [DQ-08] | Pass | 0.001 |
| UT-FC-042 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_sample_passes_lifecycle_rules[DQ-09] | Sample passes lifecycle rules [DQ-09] | Pass | 0.001 |
| UT-FC-043 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_sample_passes_lifecycle_rules[DQ-10] | Sample passes lifecycle rules [DQ-10] | Pass | 0.001 |
| UT-FC-044 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_sample_passes_lifecycle_rules[DQ-11] | Sample passes lifecycle rules [DQ-11] | Pass | 0.002 |
| UT-FC-045 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_incomplete_lifecycle_is_rejected[Digital Fraud,Confirmed Fraud,8/4/2026 16:00-Digital Fraud,Confirmed Fraud,-FC0000002] | Incomplete lifecycle is rejected [Digital Fraud,Confirmed Fraud,8/4/2026 16:00-Digital Fraud,Confirmed Fraud,-FC0000002] | Pass | 0.186 |
| UT-FC-046 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_incomplete_lifecycle_is_rejected[Medium,$237.19 ,$0.00 ,Deposit Ops,,-Medium,$237.19 ,$0.00 ,Deposit Ops,False Positive,-FC0000001] | Incomplete lifecycle is rejected [Medium,$237.19 ,$0.00 ,Deposit Ops,,-Medium,$237.19 ,$0.00 ,Deposit Ops,False Positive,-FC0000001] | Pass | 0.196 |
| UT-FC-047 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_incomplete_lifecycle_is_rejected[Enhanced Review,False Positive,8/6/2026 0:00-Enhanced Review,,8/6/2026 0:00-FC0000003] | Incomplete lifecycle is rejected [Enhanced Review,False Positive,8/6/2026 0:00-Enhanced Review,,8/6/2026 0:00-FC0000003] | Pass | 0.184 |
| UT-FC-048 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_close_before_open_is_rejected | Close before open is rejected | Pass | 0.184 |
| UT-FC-049 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_confirmed_above_suspected_is_rejected | Confirmed above suspected is rejected | Pass | 0.193 |
| UT-FC-050 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_false_positive_with_loss_warns_and_keeps_case | False positive with loss warns and keeps case | Pass | 0.198 |
| UT-FC-051 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_confirmed_fraud_without_loss_warns_by_default | Confirmed fraud without loss warns by default | Pass | 0.217 |
| UT-FC-052 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_confirmed_fraud_without_loss_can_be_rejected | Confirmed fraud without loss can be rejected | Pass | 0.293 |
| UT-FC-053 | FR-03 Lifecycle and loss checks | SCRUM-28 | tests/test_lifecycle.py | test_cases_opened_after_run_date_are_rejected | Cases opened after run date are rejected | Pass | 0.122 |
| UT-FC-054 | FR-04 Link to Member 360 | SCRUM-29 | tests/test_member_link.py | test_member_found_flag | Member found flag | Pass | 0.001 |
| UT-FC-055 | FR-04 Link to Member 360 | SCRUM-29 | tests/test_member_link.py | test_unmatched_cases_are_kept_and_reported | Unmatched cases are kept and reported | Pass | 0.001 |
| UT-FC-056 | FR-04 Link to Member 360 | SCRUM-29 | tests/test_member_link.py | test_member_rule_warns_without_blocking | Member rule warns without blocking | Pass | 0.002 |
| UT-FC-057 | FR-04 Link to Member 360 | SCRUM-29 | tests/test_member_link.py | test_match_rate_recorded_without_blocking_by_default | Match rate recorded without blocking by default | Pass | 0.001 |
| UT-FC-058 | FR-04 Link to Member 360 | SCRUM-29 | tests/test_member_link.py | test_match_rate_below_minimum_blocks_and_keeps_previous_product | Match rate below minimum blocks and keeps previous product | Pass | 0.202 |
| UT-FC-059 | FR-04 Link to Member 360 | SCRUM-29 | tests/test_member_link.py | test_missing_member_reference_fails_clearly | Missing member reference fails clearly | Pass | 0.003 |
| UT-FC-060 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_days_to_close | Days to close | Pass | 0.001 |
| UT-FC-061 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_case_age_days | Case age days | Pass | 0.001 |
| UT-FC-062 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_loss_confirmation_ratio | Loss confirmation ratio | Pass | 0.001 |
| UT-FC-063 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_known_cases | Known cases | Pass | 0.005 |
| UT-FC-064 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_metrics_null_by_lifecycle | Metrics null by lifecycle | Pass | 0.004 |
| UT-FC-065 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_sample_metric_ranges | Sample metric ranges | Pass | 0.003 |
| UT-FC-066 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_sla_days_by_priority | Sla days by priority | Pass | 0.001 |
| UT-FC-067 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_sla_breached_flag | Sla breached flag | Pass | 0.002 |
| UT-FC-068 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_open_breaches_reported_by_priority | Open breaches reported by priority | Pass | 0.004 |
| UT-FC-069 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_closed_cases_within_sla | Closed cases within sla | Pass | 0.001 |
| UT-FC-070 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_former_critical_only_exception_is_gone | Former critical only exception is gone | Pass | 0.001 |
| UT-FC-071 | FR-05 Derived case metrics | SCRUM-30 | tests/test_metrics.py | test_sla_days_are_configurable | Sla days are configurable | Pass | 0.119 |
| UT-FC-072 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_all_cases_published | All cases published | Pass | 0.001 |
| UT-FC-073 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_blocking_rules_pass[DQ-01] | Blocking rules pass [DQ-01] | Pass | 0.001 |
| UT-FC-074 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_blocking_rules_pass[DQ-02] | Blocking rules pass [DQ-02] | Pass | 0.001 |
| UT-FC-075 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_blocking_rules_pass[DQ-03] | Blocking rules pass [DQ-03] | Pass | 0.001 |
| UT-FC-076 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_blocking_rules_pass[DQ-04] | Blocking rules pass [DQ-04] | Pass | 0.001 |
| UT-FC-077 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_blocking_rules_pass[DQ-05] | Blocking rules pass [DQ-05] | Pass | 0.001 |
| UT-FC-078 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_every_rule_recorded | Every rule recorded | Pass | 0.001 |
| UT-FC-079 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_product_table_declares_contract_types | Product table declares contract types | Pass | 0.002 |
| UT-FC-080 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_csv_starts_with_sample_columns | Csv starts with sample columns | Pass | 0.033 |
| UT-FC-081 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_csv_value_formats | Csv value formats | Pass | 0.002 |
| UT-FC-082 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_data_contract | Data contract | Pass | 0.004 |
| UT-FC-083 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_contract_declares_eastern_time | Contract declares eastern time | Pass | 0.003 |
| UT-FC-084 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_committed_ddl_matches_contracts | Committed ddl matches contracts | Pass | 0.004 |
| UT-FC-085 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_blocking_failure_keeps_previous_product | Blocking failure keeps previous product | Pass | 0.212 |
| UT-FC-086 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_rerun_is_idempotent | Rerun is idempotent | Pass | 0.24 |
| UT-FC-087 | FR-06 Publish and govern | SCRUM-31 | tests/test_publish.py | test_run_log_reconciles | Run log reconciles | Pass | 0.002 |
| UT-FC-088 | FR-06 Publish and govern (routing check) | SCRUM-31 | tests/test_routing.py | test_routing_check_off_by_default | Routing check off by default | Pass | 0.001 |
| UT-FC-089 | FR-06 Publish and govern (routing check) | SCRUM-31 | tests/test_routing.py | test_routing_matrix_flags_unexpected_queue | Routing matrix flags unexpected queue | Pass | 0.114 |
| UT-FC-090 | FR-06 Publish and govern (routing check) | SCRUM-31 | tests/test_routing.py | test_case_types_outside_matrix_are_not_checked | Case types outside matrix are not checked | Pass | 0.111 |
| UT-FC-091 | FR-06 Publish and govern (status history) | SCRUM-31 | tests/test_status_history.py | test_two_run_dates_build_history | Two run dates build history | Pass | 0.221 |
| UT-FC-092 | FR-06 Publish and govern (status history) | SCRUM-31 | tests/test_status_history.py | test_same_date_rerun_is_idempotent | Same date rerun is idempotent | Pass | 0.228 |
| UT-FC-093 | FR-06 Publish and govern (status history) | SCRUM-31 | tests/test_status_history.py | test_snapshot_columns | Snapshot columns | Pass | 0.002 |
| UT-FC-094 | FR-06 Publish and govern (status history) | SCRUM-31 | tests/test_status_history.py | test_blocked_run_writes_no_snapshot | Blocked run writes no snapshot | Pass | 0.21 |
| UT-FC-095 | FR-07 Account ID mapping | SCRUM-32 | tests/test_account_link.py | test_account_found_flag | Account found flag | Pass | 0.123 |
| UT-FC-096 | FR-07 Account ID mapping | SCRUM-32 | tests/test_account_link.py | test_unmatched_accounts_are_kept_and_reported | Unmatched accounts are kept and reported | Pass | 0.001 |
| UT-FC-097 | FR-07 Account ID mapping | SCRUM-32 | tests/test_account_link.py | test_account_unknown_to_reference_table_is_not_found | Account unknown to reference table is not found | Pass | 0.11 |
| UT-FC-098 | FR-07 Account ID mapping | SCRUM-32 | tests/test_account_link.py | test_missing_reference_table_fails_clearly | Missing reference table fails clearly | Pass | 0.004 |
| UT-FC-099 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A0001] | Any width converts to canonical [A0001] | Pass | 0.002 |
| UT-FC-100 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A00001] | Any width converts to canonical [A00001] | Pass | 0.001 |
| UT-FC-101 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A0000001] | Any width converts to canonical [A0000001] | Pass | 0.001 |
| UT-FC-102 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A1] | Any width converts to canonical [A1] | Pass | 0.001 |
| UT-FC-103 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[ A00001 ] | Any width converts to canonical [ A00001 ] | Pass | 0.001 |
| UT-FC-104 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[A12345678] | Malformed ids are rejected [A12345678] | Pass | 0.001 |
| UT-FC-105 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[X1] | Malformed ids are rejected [X1] | Pass | 0.001 |
| UT-FC-106 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[A] | Malformed ids are rejected [A] | Pass | 0.001 |
| UT-FC-107 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[A12B] | Malformed ids are rejected [A12B] | Pass | 0.001 |
| UT-FC-108 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[] | Malformed ids are rejected [] | Pass | 0.001 |
| UT-FC-109 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_same_account_across_systems_is_allowed | Same account across systems is allowed | Pass | 0.001 |
| UT-FC-110 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_collision_within_a_system_rejects_both | Collision within a system rejects both | Pass | 0.001 |
| UT-FC-111 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_unconvertible_id_is_rejected_not_mapped | Unconvertible id is rejected not mapped | Pass | 0.001 |
| UT-FC-112 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_in_core_banking_flag | In core banking flag | Pass | 0.001 |
| UT-FC-113 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_committed_table_is_current | Committed table is current | Pass | 0.004 |
| UT-FC-114 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_committed_table_contents | Committed table contents | Pass | 0.002 |
| UT-FC-115 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_committed_table_is_valid | Committed table is valid | Pass | 0.002 |
| UT-FC-116 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-duplicate key] | Validator catches problems [<lambda>-duplicate key] | Pass | 0.001 |
| UT-FC-117 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-not A + 7 digits] | Validator catches problems [<lambda>-not A + 7 digits] | Pass | 0.001 |
| UT-FC-118 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-in_core_banking] | Validator catches problems [<lambda>-in_core_banking] | Pass | 0.001 |
| UT-FC-119 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-collision] | Validator catches problems [<lambda>-collision] | Pass | 0.001 |
| UT-FC-120 | Framework | - | tests/test_framework_dq.py | test_reject_rule_removes_and_logs_rows | Reject rule removes and logs rows | Pass | 0.003 |
| UT-FC-121 | Framework | - | tests/test_framework_dq.py | test_block_rule_with_count_blocks | Block rule with count blocks | Pass | 0.002 |
| UT-FC-122 | Framework | - | tests/test_framework_dq.py | test_rule_that_does_not_apply_passes_with_zero_rows_checked | Rule that does not apply passes with zero rows checked | Pass | 0.002 |
| UT-FC-123 | Framework | - | tests/test_framework_dq.py | test_rule_that_applies_runs_normally | Rule that applies runs normally | Pass | 0.003 |
| UT-FC-124 | Framework | - | tests/test_framework_load.py | test_replace_partition_is_idempotent_and_isolated | Replace partition is idempotent and isolated | Pass | 0.03 |
| UT-FC-125 | Framework | - | tests/test_framework_load.py | test_replace_partition_rejects_unknown_column | Replace partition rejects unknown column | Pass | 0.004 |
| UT-FC-126 | Framework | - | tests/test_framework_load.py | test_failed_partition_load_rolls_back | Failed partition load rolls back | Pass | 0.02 |
| UT-FC-127 | Framework | - | tests/test_framework_sync.py | test_framework_matches_sibling_products | Framework matches sibling products | Pass | 0.01 |
