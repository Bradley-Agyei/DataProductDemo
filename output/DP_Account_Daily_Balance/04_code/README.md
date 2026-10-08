# DP_Account_Daily_Balance: code

Account Daily Balance data product (Jira epic SCRUM-35): one governed row per account per calendar day. Built on the shared `dp_framework`, the same as the other products.

Only **FR-07 publish (SCRUM-43)** is built so far. FR-01 to FR-06 (SCRUM-37 to 42) will build the product frame that `publish` takes.

## FR-07 Publish with DQ gate, exceptions and data contract (SCRUM-43)

`src/account_daily_balance/run.py: publish(product, counted_transactions, upstream_rejects)` runs these steps in order:

1. **PII guard.** Every value in any PII-named column (names, addresses, postal codes, the same list as the repo's pii gate) is replaced with `*`. A reject whose column is PII gets its `raw_value` masked, and its reason is rewritten because parse errors quote the value. The contract itself has no PII column, so these columns never reach the table or the CSV.
2. **DQ gate** (`dq_rules.py`). These rules block publishing:
   - DQ-01: key is unique and not null
   - DQ-02: ID patterns
   - DQ-03: required columns are present
   - DQ-04: allowed values
   - DQ-05: closing = opening + credits − debits
   - DQ-06: opening = previous day's closing
   - DQ-07: per-account reconciliation to the counted source transactions
   - DQ-10: overdraft flag is set correctly

   DQ-11 (available ≤ closing) only warns.
3. **Exception report.** Every upstream reject and every warning is listed with its rule ID: `dq_exceptions` table and `out/dq_exceptions.csv`.
4. **Write.**
   - Always written: rejects, DQ results and the run log (`out/run_log.csv` too).
   - Written only on SUCCESS: the product table, `out/account_daily_balance.csv` and `out/data_contract.json`/`.md`. A blocked run leaves the previous product in place.

A rerun with the same inputs replaces the product with the same rows.

## Assumptions to confirm (no PRD in the repo yet)
- **DQ-01 to DQ-04** follow the house pattern used by Member 360 and Fraud Case.
- **The 11 sample columns** are the first 11 columns of the epic's target schema (`config.SAMPLE_COLUMNS`). When `data/product/DP_Account_Daily_Balance.csv` lands, the header test checks against it instead.
- **`product_code` and `available_balance` are `pending`** in the contract (Q6 and Q5), so they're published as NULL.

## Run
```bash
pip install -r requirements.txt
pytest -q
python -m src.account_daily_balance.run --write-ddl   # regenerate sql/ddl from the contracts
```
The end-to-end run (sample data, 100 rows) needs FR-01 to FR-06.
