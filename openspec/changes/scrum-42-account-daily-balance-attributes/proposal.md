# Proposal

## Why

Finance analysts need each daily balance tagged with its product and account status so they can report balances by product. Fraud & risk analysts also need to know when a Dormant member's accounts move money. That is FR-06 (Jira SCRUM-42, PRD §8 FR-06, DQ-04, DQ-13). FR-07 (SCRUM-43) already publishes `product_code` and `account_status`, but nothing fills them yet. DQ-13 is listed in PRD §10 but has no code.

Q6 is still open: the Product team has not supplied the product code reference table. This change builds the lookup without the data. `product_code` stays NULL until the table arrives, and adding the file then needs no code change.

## What Changes

- **Account attributes (FR-06).** `account_attributes` adds `member_id`, `account_status` and `product_code` to every roll-forward row, using the account's standardized `Account` record.
  - `account_status` is copied from the current value, with no history (Q11).
  - `product_code` comes from a product code reference table keyed by `product_id`, never from hard-coded values.
- **Product code reference table.** A new contract `product_code_ref` (`product_id`, `product_code`) and a loader for `data/reference/product_code_map.csv`. The file is not part of this change.
  - When the file is absent, `product_code` is NULL and the column stays PENDING in the data contract. The run is not blocked.
  - When the file is present, it is validated (contract, duplicate `product_id`, codes in DQ-04's allowed list) before use. An account whose `product_id` has no match gets NULL `product_code` and a DQ-14 warning.
- **DQ-13 dormant activity.** One WARN per Dormant member with at least one source transaction of any status (Posted, Pending or Reversed) in the run, keyed by `member_id`. Counted (Posted-only) activity is not enough: M000004's only account has Pending transactions only, and the PRD expects M000004 to be reported. It is based on `member_status = 'Dormant'`, not on hard-coded IDs and not on `account_status`. The detail gives counts only, never Member PII.
- **Warnings into publish.** `publish()` takes the warnings FR-05 and FR-06 produce and adds them to the exception report. `dq_rules.py` already describes this path, but nothing feeds it yet.
- **Tests** separate the two rules your review flagged as confounded: a Dormant member whose account is Open, and a Restricted account whose member is Active. The sample run checks that M000004 and M000008 are reported.

Out of scope:
- Supplying the reference data (Q6). A follow-up adds `product_code_map.csv` and flips `product_code` to ready.
- Status or product history and as-of-date values for backfills (Q11).
- The end-to-end `run.py` build. It still waits for FR-01, FR-03 and FR-05.

## Capabilities

### New Capabilities

- `data-products/account-daily-balance`: the Account Daily Balance product. SCRUM-40 and SCRUM-43 add requirements to this capability in changes that are not yet archived. This change adds the account attributes, the product code lookup and the DQ-13 and DQ-14 warnings.

### Modified Capabilities

None. `openspec/specs/` holds no account-daily-balance spec yet.

## Impact

- **New:** `src/account_daily_balance/attributes.py` and a `PRODUCT_CODE_REF` contract in `contracts/`, both under `output/DP_Account_Daily_Balance/04_code/`.
- **Changed:**
  - `config.py`: path to the reference table, contract metadata.
  - `dq_rules.py`: docstring only.
  - `run.py`: `publish(..., upstream_warnings=...)`. The new parameter is optional, so existing callers still work.
  - `exceptions.py`: accepts the warnings passed in.
  - `tests/sample_inputs.py`: reads only `member_id` and `member_status` from Member.
  - `sql/ddl/`: regenerated.
  - Docs: `04_code/README.md`, `docs/kt/account-daily-balance/README.md`.
- **Unchanged:** `data/raw/` and `dp_framework`. The framework stays byte-identical to the other products' copies.
- **PII:** Member is read with `usecols=["member_id", "member_status"]`, so name and postal-code columns are never loaded.
