# Proposal

## Why

The DP_Payment_Transaction source contracts (`contracts/sources.py`) were copied from DP_Member_360, so they follow that product's PRD. PRD_Payment_Transaction.md §5 gives different physical types for 16 columns, and doesn't key `reference_number`. It also lists Member `city` as PII (§5.7), and hides Branch `city` and `postal_code` because they match member PII (§5.5). The raw layer masked neither city.

The raw files themselves already match the PRD, so they're not changed. `data/raw/` is read-only (CLAUDE.md, and enforced by the `raw` gate). A profile of the 7 source files found:
- every primary key unique and present;
- every ID in its §5 raw format;
- 0 orphan foreign keys;
- the transaction's member and branch match the account on 100 of 100 rows;
- the direction matches the transaction type on 100 of 100 rows;
- all 10 accounts present in `account_id_map`.

## What Changes

- **`contracts/sources.py`:** physical types aligned to PRD §5.
  - IDs: `transaction_type_id` and `channel_id` become `VARCHAR(5)`; `branch_id` and `product_id` become `VARCHAR(10)`.
  - `postal_code` becomes `VARCHAR(10)`, and `reference_number` becomes `VARCHAR(16)`.
  - `day_name` and `month_name` become `VARCHAR(10)`, `time_zone` becomes `VARCHAR(10)`, `account_status` becomes `VARCHAR(12)`, and `member_status` becomes `VARCHAR(10)`.
  - `reference_number` loses its `UNIQUE` key. The PRD doesn't key it, and duplicates are the DQ-12 warning. Nothing enforced `UNIQUE`, so behaviour is unchanged.
- **`config.PII_MASKED_COLUMNS`:** Member `city` (§5.7) and Branch `city` (§5.5) are masked with `*` in the raw layer, alongside the columns already masked.
- **New `tests/test_source_contract.py`:**
  - reads the §5 tables **from the PRD file itself** and checks every source contract (column order, type, key) against them, so a PRD edit that the code doesn't follow fails;
  - checks the masked Member columns against the PII columns in §5.7, and the masked Branch columns against §5.5;
  - checks raw key integrity (primary keys, ID formats, foreign keys including `Account.product_id → Product.csv`, `date_key` agreeing with `full_date`, owner and branch match, direction match, account map coverage) so a change in the source surfaces as a finding.

- **New `DP_Account_Daily_Balance/04_code/tests/test_contract_prd.py`:** checks the `account_daily_balance` contract (column order, types, key, allowed values, the 11 sample columns) against PRD_Account_Daily_Balance.md §6, read from the file. It already matched, so there's no code change there.

Every primary and foreign key already matched the PRD. The only key change is dropping `UNIQUE` from `reference_number`.

## Capabilities

### New Capabilities
- `data-products/payment-transaction`: source contracts follow the PRD, and every PII column the PRD hides is masked.
- `data-products/account-daily-balance`: the product contract is checked against its PRD.

## Impact

- `output/DP_Payment_Transaction/04_code/`: `contracts/sources.py`, `src/payment_transaction/config.py`, the tests and the README.
- `output/DP_Account_Daily_Balance/04_code/tests/test_contract_prd.py` (test only).
- `docs/kt/payment-transaction/README.md`.
- The raw layer stores every column as `TEXT`, so the type changes don't change any landed value. They matter from FR-02 (standardize) onwards.
