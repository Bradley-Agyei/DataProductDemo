# Tasks

## 1. Shared framework: partition replace

- [x] 1.1 Add `Warehouse.replace_partition(table, df, column, value)` to `output/DP_Member_360/04_code/src/dp_framework/load.py`, running create-if-missing, delete for the partition, then insert in one transaction. Verify with a new framework test: loading the same partition twice leaves one copy, and other partitions are untouched.
- [x] 1.2 Copy the updated `dp_framework/` into `output/DP_Fraud_Case/04_code/src/`. Add a test in each product asserting the framework files are byte-identical to the other product's copy (skipped when the sibling folder is absent). Verify: the test passes in both products.

## 2. Account ID mapping reference table (SCRUM-32)

- [x] 2.1 Build `data/reference/account_id_map.csv` from `Account.csv` (core_banking) and `DP_Fraud_Case.csv` (fraud_case_mgmt). Verified: 110 rows; `core_banking/A00001` and `fraud_case_mgmt/A0000001` → `A0000001`; 20 rows (10 canonical IDs) `in_core_banking` TRUE.
- [x] 2.2 Add `tools/build_account_id_map.py` (generator, using `conform_account_id`: `A` + 1–7 digits → `A` + 7) and `tools/validate_account_id_map.py` (pattern, key uniqueness, same-system collision). Verify with tests in `tools/tests/`: `A0001`/`A00001`/`A0000001` → `A0000001`; `A12345678` and `X1` rejected; one system holding `A0001` and `A00001` → both rejected as a collision; regenerating reproduces the committed CSV byte-for-byte.
- [x] 2.3 Member 360: add the `--account-ref` path and source rule DQ-11 (reject a core banking account missing from the table under `core_banking`). Verify: the sample passes DQ-11; a test with a trimmed table rejects that account with DQ-11, and its transactions cascade-reject through DQ-09.
- [x] 2.4 Add a reference-table data dictionary entry to both PRDs and update the Member 360 README, `stories.md` and PRD section 11 (account standard decided). Verify: the `pytest -q` total is reported in `stories.md` and the README run command works.

## 3. Fraud Case: time zone (Q3) and Confirmed Fraud severity (Q6)

- [x] 3.1 Add `timezone: America/New_York` to `CONTRACT_META` and "(ET)" to the timestamp column descriptions in `contracts/sources.py`. Verify: a test reads `data_contract.json` and finds the timezone and "ET" in both timestamp descriptions, and `case_open_ts` for FC0000001 is still `2026-08-01 08:00:00`.
- [x] 3.2 Record Q6 as decided (DQ-10 stays a warning; the setting stays). Verify: the existing DQ-10 warn and reject tests still pass.

## 4. Fraud Case: account linkage (Q2) and member match rate (Q1)

- [x] 4.1 Add `account_found_flag BOOLEAN` to the product contract (after `member_found_flag`), a `--account-ref` path (default `data/reference/account_id_map.csv`), `load_account_reference` (looks up `fraud_case_mgmt` rows → `in_core_banking`), and the `ACCOUNT_NOT_FOUND` exception. Copy the reference CSV into `tests/data/`. Verify with tests: FC0000001 TRUE, FC0000011 FALSE, 90 `ACCOUNT_NOT_FOUND`, a missing table fails with the file name.
- [x] 4.2 Add `Settings.min_member_match_rate` (default 0.0) and blocking rule DQ-14, with the rate and minimum in its description. Verify with tests: by default DQ-14 is Pass with "10.00%" in the description; with a minimum of 0.99 the run is BLOCKED and the previous product is kept.

## 5. Fraud Case: SLA by priority (Q5) and routing check (Q4)

- [x] 5.1 Replace `critical_sla_days` with `Settings.sla_days_by_priority` (Critical 30, High 45, Medium 60, Low 90). Add `sla_days INT` and `sla_breached_flag BOOLEAN` before the audit columns, and replace `CRITICAL_CASE_AGED` with `CASE_SLA_BREACHED` (open cases only). Verify with tests: High → `sla_days` 45; FC0000011 breached and reported; FC0000002 not breached; no `CRITICAL_CASE_AGED`; the breach count matches a hand count recorded in the test report.
- [x] 5.2 Add `Settings.allowed_queues_by_case_type` (default None) and DQ-13 (warn). Verify with tests: by default DQ-13 is Pass with 0 rows checked; with `{Card Fraud: (Card Ops,)}`, FC0000005 is counted as a failure and is still published.

## 6. Fraud Case: status history (Q7)

- [x] 6.1 Add the `FRAUD_CASE_STATUS_SNAPSHOT` contract (PK `snapshot_date`, `case_id`) and write it with `replace_partition` keyed on the run date, on SUCCESS only. Add it to `DDL_TABLES` and regenerate the DDL. Verify with tests: runs for 2026-10-04 and 2026-10-05 → 200 rows; two runs for 2026-10-04 → 100 rows; a blocked run writes no snapshot.

## 7. Fraud Case docs and generated files

- [x] 7.1 Regenerate the Fraud Case PRD and dictionary (23 product columns, DQ-13 and DQ-14, section 11 marked Decided with each decision). Update `stories.md`, `Test_Report_Fraud_Case.md`, the README and `05_PR_description.md` (BREAKING exception rename). Verify: the PRD's target table lists 23 columns and the test report numbers match the latest `pytest -q` and a real run.

- [x] 7.2 (Added at user request) Add `tools/build_unit_test_cases.py` and generate `Unit_Test_Cases_Member_360.{md,xlsx}` and `Unit_Test_Cases_Fraud_Case.{md,xlsx}` from real pytest runs: each case has an ID, story, Jira key, description and actual result. Verified: 130/130 (Member 360) and 127/127 (Fraud Case) passed, including the 21 shared tool tests in each.

## 8. Integration and delivery

- [x] 8.1 End-to-end: run Member 360, then Fraud Case with the default references, `--as-of 2026-10-04`. Verify: both exit 0; Fraud Case publishes 100 rows; DQ-01..DQ-11 and DQ-14 Pass; DQ-12 and DQ-13 as specified.
- [x] 8.2 Both original PRs (#2 SCRUM-17, #3 SCRUM-25) are already merged into `develop` and their branches deleted. So commit all follow-ups (both products, `tools/`, reference table, `openspec/`, unit test case documents) on one new branch, `feature/SCRUM-32-resolve-open-decisions`, from `origin/develop` in the ClaudeDemo clone. Re-run pytest there, then push. Verify: `git ls-remote` shows the branch, and the compare page against `develop` shows only these follow-ups.
- [x] 8.3 Comment the decisions and new test results on SCRUM-25 and SCRUM-32 (and on SCRUM-17 for DQ-11), and add SCRUM-32 to `output/DP_Fraud_Case/jira_issues.md`. Verify: the comments are visible on all three issues.
