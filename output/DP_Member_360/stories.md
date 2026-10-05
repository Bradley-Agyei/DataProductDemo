# Member 360 – stories and build status

Source: [PRD_Member_360.md](PRD_Member_360.md), section 8, with types from sections 5–6, mapping from section 7 and DQ rules from section 10.
Code: [04_code/](04_code/README.md) · Tests: `pytest -q` → 105 passed (includes account ID mapping DQ-11 and shared framework tests)

| Story | Jira | Status |
|---|---|---|
| FR-01 Ingest sources | SCRUM-18 | Built |
| FR-02 Standardize data types | SCRUM-19 | Built |
| FR-03 Conform member ID | SCRUM-20 | Built |
| FR-04 Build Member 360 core | SCRUM-21 | Built (the Restricted rule is a switch until Q5 is approved) |
| FR-05 Integrate new feeds | SCRUM-22 | Partly built: columns typed and published as NULL; blocked on feeds (Q3/Q4) |
| FR-06 Data quality and exceptions | SCRUM-23 | Built |
| FR-07 Publish and govern | SCRUM-24 | Built locally; catalog entry and access roles still to be set up on the platform |

## FR-01 Ingest sources
- [x] Raw row counts match files (10/10/10/10/10/10/100/10): `test_ingest.py::test_raw_row_counts_match_files`
- [x] Quoted values with commas stay in one column: `test_quoted_values_with_commas_stay_in_one_column`
- [x] Rerun doesn't duplicate rows: `test_rerun_does_not_duplicate_raw_rows`
- [x] Run logged with file name, rows read and rows loaded: `test_raw_rows_carry_load_metadata`, `test_dq.py::test_run_log_reconciles`
- [x] Unexpected file header fails fast: `test_unexpected_header_fails_fast`

## FR-02 Standardize data types
- [x] All 60 source columns typed per the dictionary: `test_standardize.py::test_staged_values_have_contract_types`, `test_staging_tables_declare_contract_types`
- [x] Failed conversions go to `rejects` with table, column, raw value and reason: `test_unparseable_value_is_rejected_with_reason`, `test_value_outside_allowed_list_is_rejected`
- [x] TXN000023 = -199.78, TXN000073 = -248.30: `test_negative_balances_in_parentheses`
- [x] 0 rejects on sample: `test_sample_sources_have_no_rejects`
- [x] Extra: duplicate primary keys are rejected: `test_duplicate_primary_key_rows_are_rejected`

## FR-03 Conform member ID
- [x] M0001…M0010 → M000001…M000010, 1:1: `test_member_id.py`
- [x] No duplicate target IDs; pattern `^M\d{6}$`: `test_xref_maps_every_source_member_one_to_one`, `test_product_ids_match_standard_pattern`
- [ ] Q1 (why the target sample has 100 members) — PO decision

## FR-04 Build Member 360 core
- [x] 10 rows, no duplicates: `test_build_core.py::test_one_row_per_source_member`
- [x] M000004 and M000008 → Restricted (switchable): `test_restricted_account_makes_relationship_restricted`, `test_restricted_rule_can_be_switched_off`
- [x] M000010 → NC, 2021-10-14: `test_direct_mappings`
- [x] Column types match PRD section 6: `test_publish.py::test_product_table_declares_contract_types`
- [x] No PII in product: `test_no_pii_in_product`

## FR-05 Integrate new feeds
- [ ] Source and owner agreed for each column (Q3/Q4) — **blocked**
- [x] Columns exist with final types, published as NULL, marked `pending`: `test_pending_attributes.py`
- [x] `age_band` logic ready for a DOB feed: `test_age_band`
- [x] Digital proxy (C03/C04 in last 90 days), off by default: `test_digital_proxy_*`
- [ ] Access restriction on kyc_status and risk_rating — platform task

## FR-06 Data quality and exceptions
- [x] DQ-01..DQ-10 run every load and are written to `dq_results`: `test_dq.py::test_every_rule_runs_and_is_recorded`
- [x] A critical failure stops publishing and the previous product is kept: `test_blocking_failure_keeps_previous_product`
- [x] Reject rules remove and log rows: `test_foreign_key_failures_cascade_to_transactions`, `test_future_join_date_rejects_member_row`
- [x] Known exceptions reported (2 negative balances, 20 dormant/restricted transactions): `test_exception_report`
- [x] DQ-11 (SCRUM-32): every core banking account is in the account ID mapping reference table; an unmapped account is rejected and its transactions cascade through DQ-09: `test_sample_accounts_are_all_mapped`, `test_account_missing_from_reference_table_is_rejected`, `test_missing_reference_table_fails_clearly`

## FR-07 Publish and govern
- [x] Data contract (JSON + MD) with every column, type, nullability, allowed values and status: `test_data_contract_lists_every_column_with_type`
- [x] CSV export matches the sample product's column order: `test_csv_matches_sample_product_shape`
- [x] Idempotent reruns: `test_rerun_is_idempotent`
- [x] DDL generated from contracts and kept in sync: `test_committed_ddl_matches_contracts`
- [ ] Catalog entry, access roles tested, consumer sign-off — platform and people tasks
