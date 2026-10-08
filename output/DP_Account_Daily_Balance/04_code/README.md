# DP_Account_Daily_Balance: code

Account Daily Balance data product (Jira epic SCRUM-35, PRD `../PRD_Account_Daily_Balance.md`): one governed row per account per calendar day. Built on the shared `dp_framework`, the same as the other products.

**FR-01 raw ingestion (SCRUM-37)** and **FR-07 publish (SCRUM-43)** are built so far. FR-02 to FR-06 (SCRUM-38 to 42) will build the product frame that `publish` takes.

## FR-01 Ingest core banking extracts (SCRUM-37)

`src/account_daily_balance/raw.py: build()` reads the 6 core banking extracts from `data/raw/` (Account, Transaction, Transaction_Type, Product, Member, Date), checks every header, and lands each as a `raw_<name>` table with every column as text:

1. **Header gate.** All files are read and header-checked by `dp_framework.ingest` before anything is written. A renamed or missing column, or a missing file, raises `SchemaError` and leaves no database and no `out/` behind.
2. **PII drop.** PII columns (Member `first_name`, `last_name`, `city`, `postal_code`: those `config.is_pii_column` finds, plus `city`, which PRD §5.5 types as PII) are dropped in memory after the header check and before the write. No PII name or value lands in the raw layer.
3. **Load columns.** Each row carries `source_file`, `dp_load_ts` and `dp_batch_id`.
4. **Row counts.** `out/raw_manifest.json` records rows per file (Account 10, Transaction 100, others 10) and how many PII columns were dropped, never a row value or PII column name.

A rerun replaces the raw tables. `account_id_map` is not an FR-01 source.

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
python -m src.account_daily_balance.raw                    # FR-01: land the 6 extracts in raw
python -m src.account_daily_balance.run --write-ddl        # regenerate sql/ddl from the contracts
```
The end-to-end run (sample data, 100 rows) needs FR-01 to FR-06.
