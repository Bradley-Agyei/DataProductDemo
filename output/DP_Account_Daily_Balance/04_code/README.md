# DP_Account_Daily_Balance: code

Account Daily Balance data product (Jira epic SCRUM-35, PRD `../PRD_Account_Daily_Balance.md`): one governed row per account per calendar day. Built on the shared `dp_framework`, the same as the other products.

**FR-02 standardization (SCRUM-38)**, **FR-04 roll-forward (SCRUM-40)**, **FR-06 account attributes (SCRUM-42)** and **FR-07 publish (SCRUM-43)** are built. FR-01 (SCRUM-37), FR-03 (SCRUM-39) and FR-05 (SCRUM-41) will complete the pipeline. `product_code` waits on Q6 (see FR-06).

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

## FR-06 Account attributes (SCRUM-42)

`src/account_daily_balance/attributes.py` runs between the roll-forward and publish.

- `account_attributes(balances, accounts, product_ref=None)` adds `member_id`, `account_status` and `product_code` to every roll-forward row from the standardized Account frame. It returns `(rows, warnings)` and raises if a balance row's account isn't in Account.
  - `account_status` is the Account value on the run date, applied to every day (no history, Q11). DQ-04 blocks anything other than Open or Restricted.
  - `product_code` is looked up by `product_id` in the product code reference table. No code is hard-coded in the pipeline; `PRODUCT_CODES` is only DQ-04's allowed list.
- `load_product_code_ref()` reads `data/reference/product_code_map.csv` (`config.PRODUCT_CODE_MAP_PATH`).
  - **While the file is absent** (Q6 open), it returns `None`: `product_code` is NULL, the contract keeps it `pending`, and the run is not blocked.
  - **When the Product team supplies it**, drop it in with columns `product_id,product_code`. It's validated against `contracts/sources.py: PRODUCT_CODE_REF`. A duplicate `product_id`, a missing value or a code outside DQ-04's allowed list stops the run with an error naming the row, before anything is published.
  - An account whose `product_id` is missing or not in the table gets NULL `product_code` and a **DQ-14** warning (one per account). DQ-14 is not in PRD §10 yet and needs PO sign-off.
- `dormant_activity(accounts, members, transactions)` raises **DQ-13** once per Dormant member (`member_status`) with at least one transaction of **any** status in the run, keyed by `member_id`. Any status, not Posted only: A0000004 (M000004) has Pending transactions only, and the PRD expects M000004 reported. The detail gives counts only; `members` needs just `member_id` and `member_status`.

Both warning lists go to `publish(..., upstream_warnings=...)`.

Tests in `tests/test_attributes.py`: the reference table loader, lookup, DQ-13 and DQ-14 on small frames (including a Dormant member with an Open account and an Active member with a Restricted account, which the sample can't separate), and the sample acceptance: DQ-13 reports exactly M000004 and M000008, 8 Open and 2 Restricted accounts, and `product_code` NULL with the run SUCCESS.

**When Q6 lands:** flip `product_code` to ready in the contract. DQ-03 will then block the NULLs that DQ-14 allows, so that change must decide whether unmatched products block or the column becomes nullable.

## FR-07 Publish with DQ gate, exceptions and data contract (SCRUM-43)

`src/account_daily_balance/run.py: publish(product, counted_transactions, upstream_rejects, upstream_warnings)` runs these steps in order:

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
3. **Exception report.** Every upstream reject and every warning is listed with its rule ID: `dq_exceptions` table and `out/dq_exceptions.csv`. Upstream warnings (DQ-13, DQ-14 from FR-06) are added as they are and get one row each in the DQ results; they never block.
4. **Write.**
   - Always written: rejects, DQ results and the run log (`out/run_log.csv` too).
   - Written only on SUCCESS: the product table, `out/account_daily_balance.csv` and `out/data_contract.json`/`.md`. A blocked run leaves the previous product in place.

A rerun with the same inputs replaces the product with the same rows.

## Checked against the PRD
- **DQ-01 to DQ-04 and DQ-10** are as PRD §10 defines them.
- **DQ-07** reconciles credits and debits separately, as PRD §10 says, so offsetting errors can't cancel out.
- **The 11 sample columns** in `config.SAMPLE_COLUMNS` are the first 11 columns in PRD §6. The target sample is shape only (Q1) and isn't committed yet. When it lands in `data/product/DP_Account_Daily_Balance.csv`, the header test checks against it instead. The PRD names the folder `data/output/product/`.
- **`product_code` and `available_balance` are `pending`** in the contract, because Q6 and Q5 block them. They're published as NULL.
- **DQ-13** is as PRD §10 defines it ("Dormant member with activity"), reported once per member and counting any transaction status. **DQ-14** is new (unmatched `product_id`, warning) and needs adding to the PRD.

## Run
```bash
pip install -r requirements.txt
pytest -q
python -m src.account_daily_balance.run --write-ddl   # regenerate sql/ddl from the contracts
```
`pytest -q` includes FR-02 sample and conversion tests, the FR-04 and FR-06 sample acceptance tests (100 rows via the test loader) and all FR-07 tests. The end-to-end run (full product CSV to `data/product/`) needs FR-01, FR-03 and FR-05 wired into `publish()`.
