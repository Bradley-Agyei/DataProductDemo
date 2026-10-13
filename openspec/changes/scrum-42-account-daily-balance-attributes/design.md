# Design

## Context

All paths are under `output/DP_Account_Daily_Balance/04_code/`.

- `roll_forward()` (FR-04) returns one row per account-day: `balance_date`, `account_id`, balances, totals and any extra columns passed through. It has no account attributes.
- `publish()` (FR-07) expects the full product frame. Today the test fixture fills `member_id`, `product_code` and `account_status` by hand.
- `standardize_sources()` (FR-02) already yields typed `Account` (with `product_id`, `account_status`, conformed `member_id`), `Member` (non-PII columns only) and `Transaction` frames.
- The contract has `product_code` as `status=PENDING` with `allowed=PRODUCT_CODES`. DQ-03 skips pending columns. DQ-04 ignores NULLs and blocks on anything outside the allowed lists.
- `exceptions.from_warnings` only handles `Rule` objects whose check runs over the product frame. A rule can report either one row per product row, keyed by `account_id|balance_date`, or a single count for the whole table. Neither can produce one row per member.
- `dq_rules.py` already says DQ-12 and DQ-13 "reach the exception report through the ... warnings passed to publish". `publish` has no such parameter yet.

## Goals / Non-Goals

**Goals:**
- The attribute step is pure: frames in, frames out, no I/O. It can be tested without `data/raw/`.
- The Q6 hand-off is a data drop: adding `data/reference/product_code_map.csv` starts the lookup with no code change.
- `dp_framework` stays untouched, so the sync test still passes.

**Non-Goals:**
- Flipping `product_code` from PENDING to READY. That needs the real table and its own change (see Risks).
- DQ-12 (FR-05). The warning path is built generically, but only DQ-13 and DQ-14 use it here.

## Decisions

### D1. A separate `attributes.py` step runs after roll-forward
`account_attributes(balances, accounts, product_ref=None) -> (frame, warnings)` left-joins the standardized Account frame on `account_id`. It adds `member_id`, `account_status` and `product_code` (via `product_id`), then drops `product_id`.
- *Why:* FR-04 stays about balances only, and its tests don't change. FR-06 gets a single home that the future `run.py` orchestration calls between roll-forward and publish.
- *Alternative:* add the columns inside `roll_forward`. Rejected because it mixes two stories and would force FR-04's tests to carry Account fixtures.
- An account in the balances with no Account row raises `ValueError`. That can't happen when the spine is built from Account, so it signals a wiring bug, not bad data.

### D2. The reference table gets a contract and is validated through the framework
Add `PRODUCT_CODE_REF = Table("product_code_ref", ...)` to `contracts/sources.py`:
- `product_id` CHAR(4), primary key;
- `product_code` VARCHAR(12), `allowed=PRODUCT_CODES`, imported from the product contract so both share one list.

`load_product_code_ref(path=config.PRODUCT_CODE_MAP_PATH)`:
- returns `None` when the file doesn't exist;
- otherwise reads it as text with `utf-8-sig`, runs `dp_framework.standardize` against the contract, and raises `ValueError` on any reject or duplicate `product_id`.

- *Why raise:* a bad reference table is a configuration error, not row-level data. Rejecting one row would quietly NULL the codes for a whole product, so the run should stop loudly. This is the same reasoning `_account_id_map` uses for `account_id_map.csv`.
- *Why `PRODUCT_CODES` stays in code:* the ticket's first two acceptance criteria conflict, as your review noted. The fix here: the mapping lives only in the table, and the allowed list stays as the DQ-04 guard on the published contract (PRD §6). The table can't introduce a code the published contract doesn't allow. Adding a new code is a contract change with 30 days' notice (CONTRACT_META).

### D3. Pending stays static in the contract
The contract keeps `status=PENDING`, so `data_contract.json` says pending whether or not a reference table is present. When the table is absent, `product_code` is all NULL, which DQ-03 (it skips pending columns) and DQ-04 (it ignores NULLs) both pass.
- *Alternative:* switch the status at run time depending on whether the file exists. Rejected because the published contract must not change shape between runs. Flipping to READY is a deliberate, versioned contract change.

### D4. DQ-13 and DQ-14 are computed in FR-06 and passed into publish
`account_attributes` returns warning records in the exception-report shape: `exception_type`, `rule_id`, `table_name`, `row_key`, `detail`.
- `publish(..., upstream_warnings=None)` passes them to `find_exceptions`, which appends them after the rejects and rule warnings.
- For each upstream rule ID, `publish` also adds one summary row to `dq_results`: severity WARN, `rows_failed` = warning count, and the existing Warn status label. The run's DQ audit then shows DQ-13 and DQ-14 next to DQ-01 to DQ-11.

- *Why not a `Rule`:* a rule check runs over the product frame, and the exception code builds every row key from the product's primary key. Reporting once per member would mean a member-level frame and contract inside the product rule set, or changing `dp_framework`. Precomputed warnings match what `dq_rules.py` already describes.
- *Signature:* `dormant_activity(accounts, members, transactions) -> list[dict]`. It joins accounts to members on `member_id` and keeps members whose `member_status == "Dormant"` and who own an account with **any** Transaction row (Posted, Pending or Reversed). It emits one record per member: row key `member_id`, detail `"Dormant member with activity: N transactions on M accounts"`.
- *Why any status:* M000004's only account (A00004) has 10 Pending transactions and no Posted ones (verified against `data/raw/`, and noted in PRD Q4). With Posted-only counting, the PRD acceptance criterion would fail.
- *Run window:* the caller passes the run's transactions, so "in the run" means whatever FR-01 extracted. On the 10-day sample that is all of them.

### D5. DQ-14 is a new rule ID
PRD §10 stops at DQ-13 and does not define what happens to an unmatched `product_id`. The new rule: one WARN per account, keyed by `account_id`, with NULL `product_code`. It fires only when a reference table is present. Without a table, every account would warn, which is just noise while Q6 is open.
- Recorded as an assumption that needs PO sign-off (see Open Questions). A warning was chosen over blocking because one missing product shouldn't hold up every other account's balance.

### D6. The sample loader reads only non-PII Member columns
`tests/sample_inputs.py` adds `load_members()`, which reads `Member.csv` with `usecols=["member_id", "member_status"]`. The PII columns are never parsed into memory. Member IDs are conformed the same way as in FR-02. The module docstring changes "Member is never opened" to say exactly which columns are read.

## Risks / Trade-offs

- **[Risk]** When Q6 lands and `product_code` becomes READY, DQ-03 will block on the NULL `product_code` that DQ-14 leaves for unmatched accounts. → The follow-up change must decide whether the column becomes nullable or unmatched rows block. Noted in the README and the KT doc.
- **[Risk]** Tests could pass because of how the sample data happens to line up. In the sample, the only Restricted accounts belong to the only Dormant members. → Unit fixtures add a Dormant member with an Open account and an Active member with a Restricted account (spec scenarios).
- **[Trade-off]** `account_status` is the current value applied to every historical day (Q11). A backfill shows today's status on past dates. Accepted per the PRD and documented in the column description.
- **[Risk]** DQ-13 also exists in the Fraud Case PRD with a different meaning. → Rule IDs are scoped per product: each product has its own `dq_exceptions` table and `table_name`. The KT doc says so; no renaming.
- **[Trade-off]** Upstream warnings bypass `run_rules`, so their logic isn't in `product_rules()`. → They are unit-tested in `test_attributes.py`, and the `dq_rules.py` docstring points there.

## Migration Plan

Nothing to migrate.
- The new `publish` parameter is optional with a default, so existing tests and callers are unchanged.
- The DDL is regenerated, but no columns change (the contract is unchanged apart from descriptions).
- Rollback: revert the commit.

## Open Questions

- DQ-14 needs PO sign-off on the ID and on warn vs block. Changing either swaps a constant and a severity; the approach stays the same.
- The format of the reference file the Product team will supply (column names, CSV vs table) is unknown. The loader expects `product_id,product_code`. A different shape only changes the loader's column mapping.
