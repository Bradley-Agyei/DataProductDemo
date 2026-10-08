# Tasks

## 1. FR-04 roll-forward (SCRUM-40)

- [x] 1.1 Add `calendar_spine` to `src/account_daily_balance/roll_forward.py`: every Date row × every account open on that day. Verify: `test_sample_has_one_row_per_account_per_day`, `test_account_not_open_has_no_rows_before_open_date`.
- [x] 1.2 Add `roll_forward`:
  - day 1 opens at `config.FIRST_DAY_OPENING_COLUMN`, later days at the prior closing;
  - closing = opening + credits − debits, and days without activity carry the balance;
  - extra total columns pass through, zero-filled;
  - it fails on totals outside the spine.

  Verify: `test_first_day_opens_at_current_balance`, `test_opening_equals_previous_closing`, `test_closing_is_opening_plus_credits_minus_debits`, `test_day_without_activity_carries_balance`, `test_extra_total_columns_pass_through_zero_filled`, `test_totals_outside_spine_raise`, `test_missing_opening_balance_raises`, `test_duplicate_totals_raise`, `test_negative_closing_allowed`.
- [x] 1.3 Add the test-only sample loader `tests/sample_inputs.py`, which stands in for FR-01 to FR-03 and counts Posted only. Run the Jira acceptance criteria on the sample. Verify: `test_sample_passes_dq05_and_dq06`, `test_sample_a0000001_roll_forward`, `test_balance_after_does_not_affect_output`.

## 2. Docs

- [x] 2.1 Update `04_code/README.md` and `docs/kt/account-daily-balance/README.md`: how the roll-forward works, Q2/Q3/Q7 assumptions, and gaps until FR-01 to FR-03 land.
