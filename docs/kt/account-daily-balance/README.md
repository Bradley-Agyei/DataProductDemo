# Account Daily Balance data product: knowledge transfer

## What this is

`DP_Account_Daily_Balance` (Jira epic SCRUM-35) will publish one governed row per account per calendar day: opening, credits, debits, closing, available balance and overdraft flag. Its users are Finance & reporting and Fraud & risk. It's the fourth product on `dp_framework`.

**FR-04, roll-forward (SCRUM-40)** and **FR-07, publish (SCRUM-43)** exist so far. FR-07 is the gate and outputs; FR-04 builds the balance chain.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Account_Daily_Balance/04_code/` | Contract, publish step, roll-forward, DQ rules and tests | `04_code/README.md` |
| `openspec/changes/scrum-40-account-daily-balance-roll-forward/` | FR-04 requirements and scenarios | `proposal.md` |
| `openspec/changes/scrum-43-account-daily-balance-publish/` | FR-07 requirements and scenarios | `proposal.md` |
| Jira SCRUM-37 to SCRUM-42 | FR-01 to FR-03 (ingest, standardize, totals), FR-05 to FR-06 (overdraft, attributes) | the stories |

## How the roll-forward works

`roll_forward(accounts, dates, daily_totals)` in `src/account_daily_balance/roll_forward.py` produces one row per account per calendar day:

1. **Calendar spine:** cross join of Date rows × Account rows, filtered to `open_date ≤ balance_date`.
2. **Opening balance:** day 1 opens at `Account.current_balance` (Q2); later days open at the prior day's closing (DQ-06).
3. **Closing balance:** opening + total_credits − total_debits (DQ-05). Days without activity carry the opening balance unchanged.
4. **Source `balance_after` is ignored** (Q3): the function takes daily totals only, never transactions, so source running balances can't reach it.
5. **Pass-through columns:** any columns from `daily_totals` other than the key and totals (e.g., `transaction_count`) are carried forward, zero-filled on days with no activity.

`daily_totals` is the interface FR-03 must produce: one row per account-day with activity, with `account_id`, `balance_date`, `total_credits` and `total_debits` (Decimal, summed separately, never netted). The roll-forward raises on duplicate keys, on activity outside the spine (dropping it would break DQ-07), and on a missing opening balance.

## How publishing works

`publish(product, counted_transactions, upstream_rejects)` in `src/account_daily_balance/run.py`:

1. **PII guard.** Any PII-named column is masked with `*`, and so is the raw value of a reject on a PII column.
2. **DQ gate.** DQ-01 to 07 and DQ-10 block publishing. DQ-11 only warns.
3. **Exception report.** Upstream rejects and the warnings are listed with their rule IDs.
4. **Write.**
   - Always written: the ops tables (rejects, DQ results, run log) and the exception report.
   - Written only on SUCCESS: the product table, the CSV and the data contract. That's why a blocked run leaves the previous product in place.

`counted_transactions` must hold one row per counted transaction, with `account_id` and `signed_amount` (credit positive, debit negative). FR-03 produces it, and DQ-07 reconciles against it.

## Things to know

- **PRD not on `develop` yet.** `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md` is on branch `feature/SCRUM-43-prd-and-dq07`, not yet merged. The contract comes from the epic's target-schema table.
  - DQ-01 to 04 are assumed to follow the house pattern.
  - The 11 sample columns are assumed to be the first 11 schema columns.
  - Check both assumptions when the PRD lands.
- **Pending columns.** `product_code` (Q6) and `available_balance` (Q5) are `pending`, so they're published as NULL until their stories are unblocked.
- **Assumptions awaiting sign-off:**
  - **Q2 (Finance):** `Account.current_balance` is the opening balance of the first day. Configurable in `config.FIRST_DAY_OPENING_COLUMN`.
  - **Q3 (source owner):** `Transaction.balance_after` is ignored; balances are recomputed from daily totals.
  - **Q7 (PO):** one row per account per calendar day (10 × 10 = 100 on the sample), with balances carried forward.
- **Gaps until other stories land:**
  - **FR-01 to FR-03 not built:** sample acceptance tests run via a test-only loader (`tests/sample_inputs.py`); counts Posted only (Q4 default). Delete the loader when SCRUM-39 lands.
  - **FR-05, FR-06 columns missing:** `overdraft_flag`, `available_balance`, `member_id`, `account_status`, `product_code` are not produced, so only DQ-05 and DQ-06 are verified on FR-04 output.
  - **DQ-07 not exercised:** needs `counted_transactions` from FR-03.
  - **Q4, Q8 may change numbers:** if Pending or Reversed count, or if sign convention differs for loans and credit cards, balances for A0000004, A0000005, A0000007–A0000010 change.
  - **Design limits:** full rebuild only (no incremental), no close date in the source, so closed accounts keep getting rows, single currency.
- **No end-to-end run yet.** The sample acceptance (100 rows, DQ-05/06 pass) runs via the loader. A full end-to-end product CSV requires FR-01 to FR-06 to wire into `publish()`. Until then, FR-07 is tested on a 2-account, 3-day fixture in `tests/conftest.py`.
