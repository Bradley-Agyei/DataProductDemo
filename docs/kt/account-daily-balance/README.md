# Account Daily Balance data product: knowledge transfer

## What this is

`DP_Account_Daily_Balance` (Jira epic SCRUM-35) will publish one governed row per account per calendar day: opening, credits, debits, closing, available balance and overdraft flag. Its users are Finance & reporting and Fraud & risk. It's the fourth product on `dp_framework`.

**FR-02, standardization (SCRUM-38)**, **FR-04, roll-forward (SCRUM-40)**, **FR-06, account attributes (SCRUM-42)** and **FR-07, publish (SCRUM-43)** exist so far. FR-07 is the gate and outputs; FR-02 conforms the raw sources, FR-04 builds the balance chain, and FR-06 tags each row with its member, status and product and raises the dormant-activity warning.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md` | PRD: target schema, mapping, FR-01 to FR-07, DQ rules, open questions | sections 6, 8 and 10 |
| `output/DP_Account_Daily_Balance/04_code/` | Contract, publish step, roll-forward, DQ rules and tests | `04_code/README.md` |
| `openspec/changes/scrum-40-account-daily-balance-roll-forward/` | FR-04 requirements and scenarios | `proposal.md` |
| `openspec/changes/scrum-38-standardize-conform-ids/` | FR-02 requirements and scenarios | `proposal.md` |
| `openspec/changes/scrum-43-account-daily-balance-publish/` | FR-07 requirements and scenarios | `proposal.md` |
| `openspec/changes/scrum-42-account-daily-balance-attributes/` | FR-06 requirements, scenarios and design decisions | `design.md` |
| Jira SCRUM-37, SCRUM-39 and SCRUM-41 | FR-01, FR-03 and FR-05 (ingest, totals, overdraft) | the stories |

## How source standardization works

`standardize_sources()` in `src/account_daily_balance/standardize.py` takes the
six raw frames produced by FR-01 and returns one typed frame per source plus
row-level rejects. It applies the shared framework parser and the source
contracts, conforms core banking account IDs with
`data/reference/account_id_map.csv`, and left-pads member IDs to six digits.
Invalid values and duplicate keys are rejected; an account with no eligible
mapping is rejected as `DQ-08`. The Member contract includes only fields FR-01
retains outside the raw PII boundary.

## How the roll-forward works

`roll_forward(accounts, dates, daily_totals)` in `src/account_daily_balance/roll_forward.py` produces one row per account per calendar day:

1. **Calendar spine:** cross join of Date rows × Account rows, filtered to `open_date ≤ balance_date`.
2. **Opening balance:** day 1 opens at `Account.current_balance` (Q2); later days open at the prior day's closing (DQ-06).
3. **Closing balance:** opening + total_credits − total_debits (DQ-05). Days without activity carry the opening balance unchanged.
4. **Source `balance_after` is ignored** (Q3): the function takes daily totals only, never transactions, so source running balances can't reach it.
5. **Pass-through columns:** any columns from `daily_totals` other than the key and totals (e.g., `transaction_count`) are carried forward, zero-filled on days with no activity.

`daily_totals` is the interface FR-03 must produce: one row per account-day with activity, with `account_id`, `balance_date`, `total_credits` and `total_debits` (Decimal, summed separately, never netted). The roll-forward raises on duplicate keys, on activity outside the spine (dropping it would break DQ-07), and on a missing opening balance.

## How account attributes work

`src/account_daily_balance/attributes.py` sits between the roll-forward and publish:

1. **Attributes.** `account_attributes(balances, accounts, product_ref)` joins the standardized Account frame on `account_id` and adds `member_id`, `account_status` (the current value on every day, Q11) and `product_code`.
2. **Product code.** Looked up by `product_id` in `data/reference/product_code_map.csv`, which the Product team owes (Q6). Until the file exists, `product_code` is NULL and stays `pending`, and the run is not blocked. When it arrives, it is validated first: a duplicate `product_id`, a blank value or a code outside DQ-04's list stops the run. An account with no match gets NULL and a **DQ-14** warning.
3. **Dormant activity.** `dormant_activity(accounts, members, transactions)` raises **DQ-13** once per Dormant member with at least one transaction of any status in the run.

Both warning lists are passed to `publish(..., upstream_warnings=...)`.

Why **any** status counts for DQ-13: A0000004, M000004's only account, has Pending transactions only. Counting Posted only would miss a member the PRD says must be reported, and dormant activity is a fraud signal whether or not it reaches the ledger.

## How publishing works

`publish(product, counted_transactions, upstream_rejects, upstream_warnings)` in `src/account_daily_balance/run.py`:

1. **PII guard.** Any PII-named column is masked with `*`, and so is the raw value of a reject on a PII column.
2. **DQ gate.** DQ-01 to 07 and DQ-10 block publishing. DQ-11 only warns.
3. **Exception report.** Upstream rejects, the rule warnings and the upstream warnings (DQ-13, DQ-14) are listed with their rule IDs. Upstream warnings also get one row each in the DQ results and never block.
4. **Write.**
   - Always written: the ops tables (rejects, DQ results, run log) and the exception report.
   - Written only on SUCCESS: the product table, the CSV and the data contract. That's why a blocked run leaves the previous product in place.

`counted_transactions` must hold one row per counted transaction, with `account_id` and `signed_amount` (credit positive, debit negative). FR-03 produces it, and DQ-07 reconciles against it.

## Things to know

- **PRD.** `PRD_Account_Daily_Balance.md` (Draft v0.1) is the spec. The contract follows §6, and the DQ rules follow §10. DQ-07 reconciles credits and debits separately. Things to know when reading it against the code:
  - **Paths.** The PRD writes `sources/data/raw/` and `data/output/product/`. The repo uses `data/raw/` and `data/product/`.
  - **No sample yet.** The target sample is shape only (Q1) and isn't committed, so the header test uses the first 11 columns in §6.
  - **Not traced yet.** The OpenSpec change has no `prd.md`, so spec-gate doesn't trace the ACs.
- **Contract checked against the PRD.** `tests/test_contract_prd.py` reads PRD §6 from the file and checks the contract's column order, types, key, allowed values and the 11 sample columns against it. A PRD edit that the contract doesn't follow fails the build.
- **Pending columns.** `product_code` (Q6) and `available_balance` (Q5) are `pending`, so they're published as NULL until their stories are unblocked.
- **When Q6 lands.** Add `product_code_map.csv` and flip `product_code` to ready in a follow-up change. DQ-03 will then block the NULL codes DQ-14 allows, so that change must choose: unmatched products block, or the column becomes nullable.
- **Rule IDs are per product.** DQ-13 here means "Dormant member with activity". The Fraud Case PRD uses DQ-13 for something else; each product has its own `dq_exceptions` table, so the IDs don't collide. **DQ-14** (unmatched `product_id`, warning) is new and needs PO sign-off and a line in PRD §10.
- **Assumptions awaiting sign-off:**
  - **Q2 (Finance):** `Account.current_balance` is the opening balance of the first day. Configurable in `config.FIRST_DAY_OPENING_COLUMN`.
  - **Q3 (source owner):** `Transaction.balance_after` is ignored; balances are recomputed from daily totals.
  - **Q7 (PO):** one row per account per calendar day (10 × 10 = 100 on the sample), with balances carried forward.
- **Gaps until other stories land:**
  - **FR-01 to FR-03 not built:** sample acceptance tests run via a test-only loader (`tests/sample_inputs.py`); counts Posted only (Q4 default). It reads only `member_id` and `member_status` from Member, so no PII column is parsed. Delete the loader when SCRUM-39 lands.
  - **FR-05 columns missing:** `overdraft_flag` and `available_balance` are not produced; the FR-06 sample test stands in for them to run publish end to end.
  - **DQ-07 not exercised:** needs `counted_transactions` from FR-03.
  - **Q4, Q8 may change numbers:** if Pending or Reversed count, or if sign convention differs for loans and credit cards, balances for A0000004, A0000005, A0000007–A0000010 change.
  - **Design limits:** full rebuild only (no incremental), no close date in the source, so closed accounts keep getting rows, single currency.
- **No end-to-end run yet.** The sample acceptance (100 rows, DQ-05/06 pass) runs via the loader. A full end-to-end product CSV requires FR-01 to FR-06 to wire into `publish()`. Until then, FR-07 is tested on a 2-account, 3-day fixture in `tests/conftest.py`.
