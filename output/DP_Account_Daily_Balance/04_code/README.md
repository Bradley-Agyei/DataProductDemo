# DP_Account_Daily_Balance: code

Account Daily Balance data product (Jira epic SCRUM-35, PRD `../PRD_Account_Daily_Balance.md`): one governed row per account per calendar day. Built on the shared `dp_framework`, the same as the other products.

**FR-02 standardization (SCRUM-38)**, **FR-04 roll-forward (SCRUM-40)** and **FR-07 publish (SCRUM-43)** are built. FR-01 (SCRUM-37), FR-03 (SCRUM-39) and FR-05 to FR-06 (SCRUM-41 to 42) will complete the pipeline.

## FR-02 Standardize types and conform IDs (SCRUM-38)

`src/account_daily_balance/standardize.py: standardize_sources()` accepts the six
raw frames produced by FR-01, casts them using `contracts/sources.py` and the
shared `dp_framework.standardize` parser, and returns `(typed_frames, rejects)`.
Account IDs in Account and Transaction are mapped through the `core_banking`
rows in `data/reference/account_id_map.csv`; member IDs are left-padded to six
digits. Amount strings support currency decoration and parenthesized negatives.
Dates, date keys, booleans and integer fields are parsed to their declared types.
An unmapped account is excluded with reason `DQ-08`; parse failures and all copies
of duplicate primary keys are also returned as row-level rejects.

Member's source contract contains only the non-PII columns retained by FR-01.
Source extracts remain read-only.

## FR-04 Balance roll-forward (SCRUM-40)

`src/account_daily_balance/roll_forward.py` produces one row per account per calendar day, with opening and closing balances that chain day-to-day.

- `calendar_spine(accounts, dates)`: cross join of Date rows × Account rows, filtered to accounts open on each day (100 rows on the sample: 10 accounts × 10 dates).
- `roll_forward(accounts, dates, daily_totals)`: applies opening balance (day 1 at `current_balance` per Q2, later days from prior closing), adds daily totals, computes closing = opening + credits − debits. Days without activity carry the opening balance. Any extra columns from `daily_totals` pass through, zero-filled.

`config.FIRST_DAY_OPENING_COLUMN = "current_balance"` (Q2) sets which Account column opens day 1; change it if Finance confirms otherwise.

Tests in `tests/test_roll_forward.py`:
- Unit tests on small hand-built frames (opening, closing, carry-forward, totals outside spine, etc.).
- Sample acceptance: 100 rows, DQ-05 and DQ-06 pass, A0000001 opens 09-21 at 500.00 and closes at 10,713.32, opens 09-22 at 10,713.32.
- Verification that `balance_after` is not used: scramble source values, output stays identical.

`tests/sample_inputs.py` is a test-only loader (stands in for FR-01 to FR-03) that reads `data/raw` and counts Posted transactions only. Remove when SCRUM-39 lands.

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
   - DQ-07: per account, credits and debits each reconcile to the counted source transactions
   - DQ-10: overdraft flag is set correctly

   DQ-11 (available ≤ closing) only warns.
3. **Exception report.** Every upstream reject and every warning is listed with its rule ID: `dq_exceptions` table and `out/dq_exceptions.csv`.
4. **Write.**
   - Always written: rejects, DQ results and the run log (`out/run_log.csv` too).
   - Written only on SUCCESS: the product table, `out/account_daily_balance.csv` and `out/data_contract.json`/`.md`. A blocked run leaves the previous product in place.

A rerun with the same inputs replaces the product with the same rows.

## Checked against the PRD
- **DQ-01 to DQ-04 and DQ-10** are as PRD §10 defines them.
- **DQ-07** reconciles credits and debits separately, as PRD §10 says, so offsetting errors can't cancel out.
- **The 11 sample columns** in `config.SAMPLE_COLUMNS` are the first 11 columns in PRD §6. The target sample is shape only (Q1) and isn't committed yet. When it lands in `data/product/DP_Account_Daily_Balance.csv`, the header test checks against it instead. The PRD names the folder `data/output/product/`.
- **`product_code` and `available_balance` are `pending`** in the contract, because Q6 and Q5 block them. They're published as NULL.

## Run
```bash
pip install -r requirements.txt
pytest -q
python -m src.account_daily_balance.run --write-ddl   # regenerate sql/ddl from the contracts
```
`pytest -q` includes FR-02 sample and conversion tests, the FR-04 sample acceptance tests (100 rows via the test loader) and all FR-07 tests. The end-to-end run (full product CSV to `data/product/`) needs FR-01 to FR-06 wired into `publish()`.
