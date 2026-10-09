## SCRUM-25: Fraud Case data product – PRD, contracts, build and tests

**Jira:** [SCRUM-25](https://monishapm.atlassian.net/browse/SCRUM-25) (Feature epic) · stories [SCRUM-26](https://monishapm.atlassian.net/browse/SCRUM-26)–[SCRUM-32](https://monishapm.atlassian.net/browse/SCRUM-32)
**OpenSpec:** `openspec/changes/resolve-fraud-case-open-decisions`. Specs: `openspec/specs/data-products/fraud-case`, `openspec/specs/identity/account-id-conformance`.
**Related:** SCRUM-17 (Member 360) supplies the member lookup and enforces the same account ID standard (DQ-11).

### Summary
- Builds `fraud_case`, one governed, typed row per fraud case, from the case-management extract.
- Every open question from the first build (Q1–Q7) now has a decision, and each is implemented and tested.
- Adds the shared **account ID mapping reference table** (SCRUM-32): any width of `A` + digits maps to canonical `A` + 7 digits.

### Changes in the follow-up commit
| Decision | Change |
|---|---|
| Q1 Member coverage | DQ-14 records the member match rate and blocks below `min_member_match_rate` (default 0, so it never blocks) |
| Q2 Account IDs | `data/reference/account_id_map.csv` + `tools/` generator and validator; `account_found_flag`, `ACCOUNT_NOT_FOUND` |
| Q3 Time zone | Data contract `timezone: America/New_York`; timestamp descriptions say ET; no value changes |
| Q4 Routing | Optional DQ-13 warning (off until a routing matrix is configured) |
| Q5 SLA | `sla_days` + `sla_breached_flag`; SLA by priority 30/45/60/90 days (configurable, **pending Fraud Ops sign-off**) |
| Q6 $0 Confirmed Fraud | Stays a warning (DQ-10); switchable |
| Q7 Status history | New `fraud_case_status_snapshot` table, one row per case per run date |
| Framework | `Warehouse.replace_partition`, `Rule.applies`; framework copies are checked to be identical |

### ⚠ BREAKING
- The `CRITICAL_CASE_AGED` exception is replaced by `CASE_SLA_BREACHED` (all priorities, open cases only).
- `fraud_case` grows from 20 to 23 columns (`account_found_flag`, `sla_days`, `sla_breached_flag`). The new columns are added before the audit columns.

### How to test
```bash
cd output/DP_Fraud_Case/04_code
pip install pandas pytest
pytest -q
python -m src.fraud_case.run --member-ref tests/data/member_360.csv --account-ref tests/data/account_id_map.csv --as-of 2026-10-04
cd ../../.. && python -m pytest -q tools/tests
```

### Test results
- `pytest -q` → **106 passed**; `tools/tests` → **21 passed**
- Pipeline run → **SUCCESS**:
  - 100 rows, 0 rejects
  - DQ-01..DQ-11 and DQ-14 Pass; DQ-12 Warn (90); DQ-13 Pass (not configured)
  - 207 exceptions: 90 MEMBER_NOT_FOUND, 90 ACCOUNT_NOT_FOUND, 27 CASE_SLA_BREACHED

### Still needed from the business
- Fraud Ops: confirm the SLA days per priority, and supply a routing matrix if wanted.
- Data Eng: the full member and account feeds, so match rates can rise and DQ-14's minimum can be raised.

### Checklist
- [x] Tests pass (product + tools)
- [x] DDL in sync with contracts; framework copies identical
- [x] Docs: PRD (section 11 decided), dictionary, stories, test report, README, OpenSpec specs
- [x] No secrets; no PII beyond pseudonymous IDs
