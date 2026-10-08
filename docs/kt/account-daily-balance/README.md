# Account Daily Balance data product: knowledge transfer

## What this is

`DP_Account_Daily_Balance` (Jira epic SCRUM-35) will publish one governed row per account per calendar day: opening, credits, debits, closing, available balance and overdraft flag. Its users are Finance & reporting and Fraud & risk. It's the fourth product on `dp_framework`.

Only **FR-07, publish (SCRUM-43)**, exists so far. It's the last step of the pipeline, built first so that the gate, the contract and the outputs are fixed before the steps that feed them.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Account_Daily_Balance/04_code/` | Contract, publish step, DQ rules and tests | `04_code/README.md` |
| `openspec/changes/scrum-43-account-daily-balance-publish/` | FR-07 requirements and scenarios | `proposal.md` |
| Jira SCRUM-37 to SCRUM-42 | FR-01 to FR-06: ingest, standardize, totals, roll-forward, overdraft, attributes | the stories |

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

- **No PRD in the repo.** The epic points to `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md`, which isn't committed. The contract comes from the epic's target-schema table.
  - DQ-01 to 04 are assumed to follow the house pattern.
  - The 11 sample columns are assumed to be the first 11 schema columns.
  - Check both assumptions when the PRD lands.
- **Pending columns.** `product_code` (Q6) and `available_balance` (Q5) are `pending`, so they're published as NULL until their stories are unblocked.
- **No end-to-end run yet.** The story's verify step (sample run, 100 rows) needs FR-01 to FR-06. Until then, publishing is tested on a 2-account, 3-day fixture in `tests/conftest.py`.
