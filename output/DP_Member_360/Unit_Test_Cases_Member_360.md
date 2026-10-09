# Unit Test Cases – DP_Member_360

- **Generated:** 2026-10-05 by `python -m tools.build_unit_test_cases`, from a real pytest run
- **Result:** 130 / 130 passed
- **Type:** automated pytest. Story-level tests run the pipeline on the real sample sources; Framework tests cover shared building blocks in isolation.

## Summary by story

| Story | Jira | Test cases | Passed |
|---|---|---|---|
| FR-01 Ingest sources | SCRUM-18 | 12 | 12 |
| FR-02 Standardize data types | SCRUM-19 | 46 | 46 |
| FR-03 Conform member ID | SCRUM-20 | 10 | 10 |
| FR-04 Build Member 360 core | SCRUM-21 | 7 | 7 |
| FR-05 Integrate new feeds | SCRUM-22 | 10 | 10 |
| FR-06 Data quality and exceptions | SCRUM-23 | 10 | 10 |
| FR-07 Publish and govern | SCRUM-24 | 6 | 6 |
| Shared: account ID mapping reference table | SCRUM-32 | 21 | 21 |
| Framework | - | 8 | 8 |

## Test cases

| TC ID | Story | Jira | Test file | Test case | Description / expected result | Result | Time (s) |
|---|---|---|---|---|---|---|---|
| UT-M360-001 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[account-10] | Raw row counts match files [account-10] | Pass | 0.002 |
| UT-M360-002 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[branch-10] | Raw row counts match files [branch-10] | Pass | 0.002 |
| UT-M360-003 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[channel-10] | Raw row counts match files [channel-10] | Pass | 0.002 |
| UT-M360-004 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[date-10] | Raw row counts match files [date-10] | Pass | 0.002 |
| UT-M360-005 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[member-10] | Raw row counts match files [member-10] | Pass | 0.002 |
| UT-M360-006 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[product-10] | Raw row counts match files [product-10] | Pass | 0.002 |
| UT-M360-007 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[transaction-100] | Raw row counts match files [transaction-100] | Pass | 0.002 |
| UT-M360-008 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_row_counts_match_files[transaction_type-10] | Raw row counts match files [transaction_type-10] | Pass | 0.002 |
| UT-M360-009 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_raw_rows_carry_load_metadata | Raw rows carry load metadata | Pass | 0.002 |
| UT-M360-010 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_quoted_values_with_commas_stay_in_one_column | Quoted values with commas stay in one column | Pass | 0.002 |
| UT-M360-011 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_rerun_does_not_duplicate_raw_rows | Rerun does not duplicate raw rows | Pass | 0.524 |
| UT-M360-012 | FR-01 Ingest sources | SCRUM-18 | tests/test_ingest.py | test_unexpected_header_fails_fast | Unexpected header fails fast | Pass | 0.032 |
| UT-M360-013 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Account] | Staged values have contract types [Account] | Pass | 0.001 |
| UT-M360-014 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Branch] | Staged values have contract types [Branch] | Pass | 0.001 |
| UT-M360-015 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Channel] | Staged values have contract types [Channel] | Pass | 0.001 |
| UT-M360-016 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Date] | Staged values have contract types [Date] | Pass | 0.001 |
| UT-M360-017 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Member] | Staged values have contract types [Member] | Pass | 0.001 |
| UT-M360-018 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Product] | Staged values have contract types [Product] | Pass | 0.001 |
| UT-M360-019 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Transaction] | Staged values have contract types [Transaction] | Pass | 0.002 |
| UT-M360-020 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staged_values_have_contract_types[Transaction_Type] | Staged values have contract types [Transaction_Type] | Pass | 0.001 |
| UT-M360-021 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Account] | Staging tables declare contract types [Account] | Pass | 0.002 |
| UT-M360-022 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Branch] | Staging tables declare contract types [Branch] | Pass | 0.002 |
| UT-M360-023 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Channel] | Staging tables declare contract types [Channel] | Pass | 0.002 |
| UT-M360-024 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Date] | Staging tables declare contract types [Date] | Pass | 0.002 |
| UT-M360-025 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Member] | Staging tables declare contract types [Member] | Pass | 0.002 |
| UT-M360-026 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Product] | Staging tables declare contract types [Product] | Pass | 0.002 |
| UT-M360-027 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Transaction] | Staging tables declare contract types [Transaction] | Pass | 0.002 |
| UT-M360-028 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_staging_tables_declare_contract_types[Transaction_Type] | Staging tables declare contract types [Transaction_Type] | Pass | 0.002 |
| UT-M360-029 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_all_60_source_columns_are_typed | All 60 source columns are typed | Pass | 0.001 |
| UT-M360-030 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_negative_balances_in_parentheses | Negative balances in parentheses | Pass | 0.001 |
| UT-M360-031 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_sample_sources_have_no_rejects | Sample sources have no rejects | Pass | 0.001 |
| UT-M360-032 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_unparseable_value_is_rejected_with_reason | Unparseable value is rejected with reason | Pass | 0.317 |
| UT-M360-033 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_value_outside_allowed_list_is_rejected | Value outside allowed list is rejected | Pass | 0.404 |
| UT-M360-034 | FR-02 Standardize data types | SCRUM-19 | tests/test_standardize.py | test_duplicate_primary_key_rows_are_rejected | Duplicate primary key rows are rejected | Pass | 0.33 |
| UT-M360-035 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_currency_text_becomes_decimal[$500.00 -expected0] | Currency text becomes decimal [$500.00 -expected0] | Pass | 0.001 |
| UT-M360-036 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_currency_text_becomes_decimal[$1,225.35 -expected1] | Currency text becomes decimal [$1,225.35 -expected1] | Pass | 0.001 |
| UT-M360-037 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_currency_text_becomes_decimal[($199.78)-expected2] | Currency text becomes decimal [($199.78)-expected2] | Pass | 0.001 |
| UT-M360-038 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_currency_text_becomes_decimal[-12.5-expected3] | Currency text becomes decimal [-12.5-expected3] | Pass | 0.001 |
| UT-M360-039 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_currency_text_becomes_decimal[0-expected4] | Currency text becomes decimal [0-expected4] | Pass | 0.001 |
| UT-M360-040 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_non_numeric_currency_is_rejected | Non numeric currency is rejected | Pass | 0.001 |
| UT-M360-041 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_decimal_precision_is_enforced | Decimal precision is enforced | Pass | 0.001 |
| UT-M360-042 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[DATE-1/8/2019-expected0] | Parse value by type [DATE-1/8/2019-expected0] | Pass | 0.001 |
| UT-M360-043 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[DATE-2019-01-08-expected1] | Parse value by type [DATE-2019-01-08-expected1] | Pass | 0.001 |
| UT-M360-044 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[TIMESTAMP-9/2/2026 9:01-expected2] | Parse value by type [TIMESTAMP-9/2/2026 9:01-expected2] | Pass | 0.001 |
| UT-M360-045 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[BOOLEAN-TRUE-True] | Parse value by type [BOOLEAN-TRUE-True] | Pass | 0.001 |
| UT-M360-046 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[BOOLEAN-false-False] | Parse value by type [BOOLEAN-false-False] | Pass | 0.001 |
| UT-M360-047 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[INT-20260921-20260921] | Parse value by type [INT-20260921-20260921] | Pass | 0.001 |
| UT-M360-048 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[SMALLINT-2026-2026] | Parse value by type [SMALLINT-2026-2026] | Pass | 0.001 |
| UT-M360-049 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[CHAR(5)-12345-12345] | Parse value by type [CHAR(5)-12345-12345] | Pass | 0.001 |
| UT-M360-050 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_parse_value_by_type[VARCHAR(10)- A00001 -A00001] | Parse value by type [VARCHAR(10)- A00001 -A00001] | Pass | 0.001 |
| UT-M360-051 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_invalid_values_raise[BOOLEAN-maybe] | Invalid values raise [BOOLEAN-maybe] | Pass | 0.001 |
| UT-M360-052 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_invalid_values_raise[DATE-31/31/2020] | Invalid values raise [DATE-31/31/2020] | Pass | 0.001 |
| UT-M360-053 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_invalid_values_raise[INT-12.5] | Invalid values raise [INT-12.5] | Pass | 0.001 |
| UT-M360-054 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_invalid_values_raise[SMALLINT-70000] | Invalid values raise [SMALLINT-70000] | Pass | 0.001 |
| UT-M360-055 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_invalid_values_raise[CHAR(2)-NCX] | Invalid values raise [CHAR(2)-NCX] | Pass | 0.001 |
| UT-M360-056 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_invalid_values_raise[VARCHAR(3)-ABCD] | Invalid values raise [VARCHAR(3)-ABCD] | Pass | 0.001 |
| UT-M360-057 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_blank_is_null | Blank is null | Pass | 0.001 |
| UT-M360-058 | FR-02 Standardize data types | SCRUM-19 | tests/test_types.py | test_postal_code_keeps_leading_zero | Postal code keeps leading zero | Pass | 0.001 |
| UT-M360-059 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_conform_member_id[M0001-M000001] | Conform member id [M0001-M000001] | Pass | 0.001 |
| UT-M360-060 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_conform_member_id[M0010-M000010] | Conform member id [M0010-M000010] | Pass | 0.001 |
| UT-M360-061 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_conform_member_id[ M42 -M000042] | Conform member id [ M42 -M000042] | Pass | 0.001 |
| UT-M360-062 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_conform_member_id[M000100-M000100] | Conform member id [M000100-M000100] | Pass | 0.001 |
| UT-M360-063 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_unconformable_ids_raise[X0001] | Unconformable ids raise [X0001] | Pass | 0.001 |
| UT-M360-064 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_unconformable_ids_raise[M] | Unconformable ids raise [M] | Pass | 0.001 |
| UT-M360-065 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_unconformable_ids_raise[M12A] | Unconformable ids raise [M12A] | Pass | 0.001 |
| UT-M360-066 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_unconformable_ids_raise[M1234567] | Unconformable ids raise [M1234567] | Pass | 0.001 |
| UT-M360-067 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_xref_maps_every_source_member_one_to_one | Xref maps every source member one to one | Pass | 0.001 |
| UT-M360-068 | FR-03 Conform member ID | SCRUM-20 | tests/test_member_id.py | test_product_ids_match_standard_pattern | Product ids match standard pattern | Pass | 0.001 |
| UT-M360-069 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_one_row_per_source_member | One row per source member | Pass | 0.251 |
| UT-M360-070 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_columns_follow_contract_order | Columns follow contract order | Pass | 0.001 |
| UT-M360-071 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_restricted_account_makes_relationship_restricted | Restricted account makes relationship restricted | Pass | 0.002 |
| UT-M360-072 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_restricted_rule_can_be_switched_off | Restricted rule can be switched off | Pass | 0.24 |
| UT-M360-073 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_direct_mappings | Direct mappings | Pass | 0.002 |
| UT-M360-074 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_audit_columns_populated | Audit columns populated | Pass | 0.001 |
| UT-M360-075 | FR-04 Build Member 360 core | SCRUM-21 | tests/test_build_core.py | test_no_pii_in_product | No pii in product | Pass | 0.001 |
| UT-M360-076 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_contract_marks_feed_columns_pending | Contract marks feed columns pending | Pass | 0.001 |
| UT-M360-077 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_pending_columns_are_null | Pending columns are null | Pass | 0.001 |
| UT-M360-078 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_not_null_check_skips_pending_columns | Not null check skips pending columns | Pass | 0.002 |
| UT-M360-079 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_age_band[birth0-18-24] | Age band [birth0-18-24] | Pass | 0.001 |
| UT-M360-080 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_age_band[birth1-None] | Age band [birth1-None] | Pass | 0.001 |
| UT-M360-081 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_age_band[birth2-35-44] | Age band [birth2-35-44] | Pass | 0.001 |
| UT-M360-082 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_age_band[birth3-65+] | Age band [birth3-65+] | Pass | 0.001 |
| UT-M360-083 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_age_band[birth4-55-64] | Age band [birth4-55-64] | Pass | 0.001 |
| UT-M360-084 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_digital_proxy_uses_recent_online_or_mobile_activity | Digital proxy uses recent online or mobile activity | Pass | 0.254 |
| UT-M360-085 | FR-05 Integrate new feeds | SCRUM-22 | tests/test_pending_attributes.py | test_digital_proxy_ignores_activity_outside_lookback | Digital proxy ignores activity outside lookback | Pass | 0.222 |
| UT-M360-086 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_every_rule_runs_and_is_recorded | Every rule runs and is recorded | Pass | 0.003 |
| UT-M360-087 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_sample_passes_all_rules | Sample passes all rules | Pass | 0.001 |
| UT-M360-088 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_foreign_key_failures_cascade_to_transactions | Foreign key failures cascade to transactions | Pass | 0.338 |
| UT-M360-089 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_sample_accounts_are_all_mapped | Sample accounts are all mapped | Pass | 0.002 |
| UT-M360-090 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_account_missing_from_reference_table_is_rejected | Account missing from reference table is rejected | Pass | 0.233 |
| UT-M360-091 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_missing_reference_table_fails_clearly | Missing reference table fails clearly | Pass | 0.003 |
| UT-M360-092 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_future_join_date_rejects_member_row | Future join date rejects member row | Pass | 0.343 |
| UT-M360-093 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_blocking_failure_keeps_previous_product | Blocking failure keeps previous product | Pass | 0.44 |
| UT-M360-094 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_exception_report | Exception report | Pass | 0.002 |
| UT-M360-095 | FR-06 Data quality and exceptions | SCRUM-23 | tests/test_dq.py | test_run_log_reconciles | Run log reconciles | Pass | 0.002 |
| UT-M360-096 | FR-07 Publish and govern | SCRUM-24 | tests/test_publish.py | test_product_table_declares_contract_types | Product table declares contract types | Pass | 0.002 |
| UT-M360-097 | FR-07 Publish and govern | SCRUM-24 | tests/test_publish.py | test_csv_matches_sample_product_shape | Csv matches sample product shape | Pass | 0.003 |
| UT-M360-098 | FR-07 Publish and govern | SCRUM-24 | tests/test_publish.py | test_csv_value_formats | Csv value formats | Pass | 0.001 |
| UT-M360-099 | FR-07 Publish and govern | SCRUM-24 | tests/test_publish.py | test_data_contract_lists_every_column_with_type | Data contract lists every column with type | Pass | 0.005 |
| UT-M360-100 | FR-07 Publish and govern | SCRUM-24 | tests/test_publish.py | test_committed_ddl_matches_contracts | Committed ddl matches contracts | Pass | 0.003 |
| UT-M360-101 | FR-07 Publish and govern | SCRUM-24 | tests/test_publish.py | test_rerun_is_idempotent | Rerun is idempotent | Pass | 0.505 |
| UT-M360-102 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A0001] | Any width converts to canonical [A0001] | Pass | 0.002 |
| UT-M360-103 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A00001] | Any width converts to canonical [A00001] | Pass | 0.001 |
| UT-M360-104 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A0000001] | Any width converts to canonical [A0000001] | Pass | 0.001 |
| UT-M360-105 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[A1] | Any width converts to canonical [A1] | Pass | 0.001 |
| UT-M360-106 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_any_width_converts_to_canonical[ A00001 ] | Any width converts to canonical [ A00001 ] | Pass | 0.001 |
| UT-M360-107 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[A12345678] | Malformed ids are rejected [A12345678] | Pass | 0.001 |
| UT-M360-108 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[X1] | Malformed ids are rejected [X1] | Pass | 0.001 |
| UT-M360-109 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[A] | Malformed ids are rejected [A] | Pass | 0.001 |
| UT-M360-110 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[A12B] | Malformed ids are rejected [A12B] | Pass | 0.001 |
| UT-M360-111 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_malformed_ids_are_rejected[] | Malformed ids are rejected [] | Pass | 0.001 |
| UT-M360-112 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_same_account_across_systems_is_allowed | Same account across systems is allowed | Pass | 0.001 |
| UT-M360-113 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_collision_within_a_system_rejects_both | Collision within a system rejects both | Pass | 0.001 |
| UT-M360-114 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_unconvertible_id_is_rejected_not_mapped | Unconvertible id is rejected not mapped | Pass | 0.001 |
| UT-M360-115 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_in_core_banking_flag | In core banking flag | Pass | 0.001 |
| UT-M360-116 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_committed_table_is_current | Committed table is current | Pass | 0.005 |
| UT-M360-117 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_committed_table_contents | Committed table contents | Pass | 0.001 |
| UT-M360-118 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_committed_table_is_valid | Committed table is valid | Pass | 0.002 |
| UT-M360-119 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-duplicate key] | Validator catches problems [<lambda>-duplicate key] | Pass | 0.001 |
| UT-M360-120 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-not A + 7 digits] | Validator catches problems [<lambda>-not A + 7 digits] | Pass | 0.001 |
| UT-M360-121 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-in_core_banking] | Validator catches problems [<lambda>-in_core_banking] | Pass | 0.001 |
| UT-M360-122 | Shared: account ID mapping reference table | SCRUM-32 | tools/tests/test_account_id_map.py | test_validator_catches_problems[<lambda>-collision] | Validator catches problems [<lambda>-collision] | Pass | 0.001 |
| UT-M360-123 | Framework | - | tests/test_framework_dq.py | test_reject_rule_removes_and_logs_rows | Reject rule removes and logs rows | Pass | 0.003 |
| UT-M360-124 | Framework | - | tests/test_framework_dq.py | test_block_rule_with_count_blocks | Block rule with count blocks | Pass | 0.002 |
| UT-M360-125 | Framework | - | tests/test_framework_dq.py | test_rule_that_does_not_apply_passes_with_zero_rows_checked | Rule that does not apply passes with zero rows checked | Pass | 0.002 |
| UT-M360-126 | Framework | - | tests/test_framework_dq.py | test_rule_that_applies_runs_normally | Rule that applies runs normally | Pass | 0.002 |
| UT-M360-127 | Framework | - | tests/test_framework_load.py | test_replace_partition_is_idempotent_and_isolated | Replace partition is idempotent and isolated | Pass | 0.03 |
| UT-M360-128 | Framework | - | tests/test_framework_load.py | test_replace_partition_rejects_unknown_column | Replace partition rejects unknown column | Pass | 0.004 |
| UT-M360-129 | Framework | - | tests/test_framework_load.py | test_failed_partition_load_rolls_back | Failed partition load rolls back | Pass | 0.021 |
| UT-M360-130 | Framework | - | tests/test_framework_sync.py | test_framework_matches_sibling_products | Framework matches sibling products | Pass | 0.008 |
