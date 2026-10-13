# Tasks

All paths are relative to `output/DP_Account_Daily_Balance/04_code/` unless stated. Run tests with the venv active: `pytest`.

## 1. Product code reference table (FR-06, Q6)

- [x] 1.1 Add the `PRODUCT_CODE_REF` contract to `contracts/sources.py`: `product_id` CHAR(4) PK, `product_code` VARCHAR(12) with `allowed=PRODUCT_CODES` imported from `contracts/account_daily_balance.py`. Add `config.PRODUCT_CODE_MAP_PATH = PROJECT_ROOT / "data" / "reference" / "product_code_map.csv"` and do **not** create the file. Verify: `test_product_code_ref_shares_allowed_codes` in `tests/test_attributes.py`.
- [x] 1.2 Add `load_product_code_ref(path)` to `src/account_daily_balance/attributes.py`:
  - returns `None` when the file is absent;
  - otherwise standardizes the table against the contract;
  - raises `ValueError` naming the offending `product_id` or code on a duplicate, missing value or disallowed code.

  Verify: `test_ref_absent_returns_none`, `test_ref_duplicate_product_id_raises`, `test_ref_code_not_allowed_raises`, `test_ref_missing_value_raises`, `test_ref_valid_loads` (fixtures written to `tmp_path`, never to `data/`).

## 2. Account attributes (FR-06)

- [x] 2.1 Add `account_attributes(balances, accounts, product_ref=None) -> (frame, warnings)`:
  - left-joins the standardized Account frame on `account_id` and adds `member_id`, `account_status` and `product_code`, then drops `product_id`;
  - raises on a balance row with no Account row.

  Verify: `test_status_copied_to_every_day`, `test_member_id_conformed`, `test_product_code_from_ref`, `test_product_code_follows_ref_not_code` (remapped P001 gives the new code), `test_product_code_null_without_ref`, `test_balance_without_account_raises`.
- [x] 2.2 Emit a DQ-14 warning per account whose `product_id` is NULL or unmatched, only when `product_ref` is given. The row key is `account_id` and the detail has no values beyond IDs. Verify: `test_unmatched_product_warns_dq14`, `test_no_dq14_without_ref`.
- [x] 2.3 Add `dormant_activity(accounts, members, transactions)`. It emits one DQ-13 warning per Dormant member with at least one Transaction row of any status, keyed by `member_id`, with the detail `"Dormant member with activity: N transactions on M accounts"`. Verify:
  - `test_dormant_pending_only_is_reported`
  - `test_dormant_with_open_account_is_reported`
  - `test_active_member_restricted_account_not_reported`
  - `test_dormant_without_activity_not_reported`
  - `test_dormant_reported_once_across_accounts_and_days`
  - `test_dormant_detail_has_no_pii`

## 3. Warnings into publish (FR-07 wiring)

- [x] 3.1 Add `upstream_warnings: list[dict] | None = None` to `publish()` in `src/account_daily_balance/run.py`:
  - `find_exceptions` in `exceptions.py` appends the warnings after the rejects and rule warnings;
  - `publish` adds one WARN summary row per upstream rule ID to `dq_results`;
  - update the `dq_rules.py` docstring to point at `attributes.py`.

  Verify: in `tests/test_publish.py`, `test_upstream_warnings_reach_exception_report` and `test_upstream_warnings_in_dq_results`, and `test_upstream_warnings_do_not_block` (status stays SUCCESS). All existing publish tests still pass unchanged.
- [x] 3.2 Update the `conftest.py` fixture so it builds the product through `account_attributes` instead of hand-setting `product_code`/`account_status`/`member_id`. Verify: the full `pytest` run is green, and `test_data_contract` still reports `product_code` and `available_balance` as pending.

## 4. Sample acceptance (Jira SCRUM-42 AC)

- [x] 4.1 Add `load_members()` to `tests/sample_inputs.py`. It reads `Member.csv` with `usecols=["member_id", "member_status"]` and conforms the IDs. Also fix the docstring's "Member is never opened" line. Verify: `test_sample_member_loader_reads_no_pii_columns` asserts the frame's columns are exactly those two.
- [x] 4.2 Run the sample through roll-forward → `account_attributes` → `dormant_activity` → `publish` with no reference table. Verify:
  - `test_sample_dormant_members_reported`: DQ-13 rows equal {M000004, M000008};
  - `test_sample_account_status_values`: 8 Open and 2 Restricted accounts, every row in the allowed list;
  - `test_sample_product_code_pending`: all NULL, run SUCCESS.

## 5. DDL and docs

- [x] 5.1 Update the `product_code` and `account_status` descriptions in the contract (reference table source, current value only per Q11). Add FR-06: SCRUM-42 to `CONTRACT_META["jira"]`. Run `python -m src.account_daily_balance.run --write-ddl`. Verify: `test_ddl_in_sync` passes and `git diff sql/ddl` shows only comment and description lines.
- [x] 5.2 Document FR-06 in `04_code/README.md` and `docs/kt/account-daily-balance/README.md`:
  - how to drop in `product_code_map.csv` (expected columns and validation);
  - the DQ-13 "any status" decision and why;
  - DQ-14 as a new rule that needs PO sign-off;
  - DQ-13 being scoped per product (vs Fraud Case);
  - the DQ-03 vs DQ-14 decision waiting for the Q6 follow-up.

  Verify: the `kt-docs` gate passes (`python tools/leftshift/checks.py kt-docs --base origin/develop`), and the docs contain no Member PII.

## 6. Integration

- [x] 6.1 Run the full gate locally: `pytest` in `04_code/`, `openspec validate scrum-42-account-daily-balance-attributes --strict`, and a commit through lefthook (`attest.py make`) without `--no-verify`. Verify: all green, `data/raw/` unchanged (`git status data/raw` clean), and the pii gate passes.

## Workflow follow-up

- Comment on SCRUM-42 with the decisions: the ticket's first two acceptance criteria resolved by D2, "activity" defined as any status, DQ-14 added, the split on Q6. Keep the `blocked-open-question` label until Q6 lands.
- Follow-up change when the Product team delivers Q6: add `data/reference/product_code_map.csv`, flip `product_code` to READY, and resolve DQ-03 vs DQ-14.
- Archive after the PR passes `ci`, `spec-gate`, `attest` and `kt-docs`.
