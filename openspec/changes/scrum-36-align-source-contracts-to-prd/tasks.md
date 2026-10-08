# Tasks

## 1. Profile raw against the PRD (read-only)

- [x] 1.1 Profile the 7 source extracts and `account_id_map` against PRD §5: primary keys, raw ID formats, foreign keys, owner, branch and direction consistency. Result: all pass, so no source finding and no change to `data/raw/`.

## 2. Align the code

- [x] 2.1 Align 16 column types in `contracts/sources.py` to PRD §5, and drop the non-PRD `UNIQUE` key on `reference_number`. The check reads §5 from the PRD file. Verify: `test_prd_lists_every_source`, and `test_source_contract_matches_prd` for each table.
- [x] 2.2 Add Member `city` (§5.7) and Branch `city` (§5.5) to `config.PII_MASKED_COLUMNS`. Verify: `test_member_pii_columns_are_masked`, `test_branch_columns_hidden_in_prd_are_masked`, `test_pii_values_are_masked`.
- [x] 2.3 Add the raw key integrity tests. Verify: `test_raw_primary_key_unique_and_present`, `test_raw_ids_match_prd_format`, `test_raw_foreign_keys_resolve` (including `Account.product_id` → Product), `test_date_key_matches_full_date`, `test_transaction_matches_account_owner_and_branch`, `test_transaction_direction_matches_type`, `test_every_account_is_in_account_id_map`.
- [x] 2.4 Add `DP_Account_Daily_Balance/04_code/tests/test_contract_prd.py`, which checks the product contract against PRD §6. Verify: `test_columns_and_types_follow_prd_order`, `test_primary_key_matches_prd`, `test_category_allowed_values_match_prd`, `test_sample_columns_are_the_first_eleven_prd_columns`.
- [x] 2.5 Run `bmad-review` (adversarial, edge-case and verification-gap lenses) on the diff and fix its findings.

## 3. Docs

- [x] 3.1 Update `04_code/README.md` and `docs/kt/payment-transaction/README.md`: the PII list now includes `city`, the contracts are pinned to the PRD, and the raw profile baseline is recorded.
