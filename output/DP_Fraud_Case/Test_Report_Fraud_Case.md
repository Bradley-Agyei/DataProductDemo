# Test Report – DP_Fraud_Case (v0.2)

- **Date:** 2026-10-05
- **Jira:** SCRUM-25 (stories SCRUM-26 to SCRUM-32)
- **OpenSpec change:** `resolve-fraud-case-open-decisions`
- **Code:** `output/DP_Fraud_Case/04_code`
- **Environment:** Python 3.14.4, pandas, pytest, SQLite

## Result
- `pytest -q` → **106 passed, 0 failed**
- Shared tooling `pytest tools/tests` → **21 passed**. These test the account ID mapping reference table.
- Real run `python -m src.fraud_case.run --as-of 2026-10-04`, using the default references (Member 360's published output and `data/reference/account_id_map.csv`) → **SUCCESS**, exit 0:
  - 100 rows published, 0 rejects
  - 207 exceptions: 90 MEMBER_NOT_FOUND, 90 ACCOUNT_NOT_FOUND, 27 CASE_SLA_BREACHED

## Test inventory
| File | Story / decision | Tests | What it proves |
|---|---|---|---|
| `test_ingest.py` | FR-01 | 5 | Row count, metadata, quoted amounts, rerun, header check |
| `test_standardize.py` | FR-02 | 9 | All 13 types; bad amount / ID / category / duplicate → rejects |
| `test_lifecycle.py` | FR-03, Q6 | 15 | DQ-06..DQ-11 on the sample and with injected bad data; DQ-10 warns by default, can be switched to reject |
| `test_member_link.py` | FR-04, Q1 | 6 | Flag counts, kept and reported, DQ-12 Warn, DQ-14 rate in description, DQ-14 blocks below a minimum |
| `test_account_link.py` | FR-07, Q2 | 4 | 10 TRUE / 90 FALSE, ACCOUNT_NOT_FOUND, unmapped ID, missing table |
| `test_metrics.py` | FR-05, Q5 | 12 | Metric functions, SLA by priority, breach flag, breaches by priority, configurable SLA |
| `test_routing.py` | Q4 | 3 | DQ-13 off by default (0 rows checked); matrix warns 15 without dropping cases |
| `test_status_history.py` | Q7 | 4 | 2 dates → 200 rows; same-date rerun → 100; columns; a blocked run writes none |
| `test_publish.py` | FR-06, Q3 | 16 | Gate, 23 typed columns, CSV, contract incl. timezone ET, DDL sync, idempotency, run log |
| `test_framework_*.py` | Framework | 8 | Partition replace, DQ engine incl. `applies`, framework copies identical |
| `test_types.py` | Framework | 24 | Shared type parsers |
| **Total** | | **106** | |

## DQ results (real run)
| Rule | Table | Severity | Checked | Failed | Status |
|---|---|---|---|---|---|
| DQ-06..DQ-11 | Fraud_Case_Extract | reject / warn | 100 | 0 | Pass |
| DQ-01..DQ-05 | fraud_case | block | 100 | 0 | Pass |
| DQ-12 | fraud_case | warn | 100 | 90 | Warn (expected: Member 360 has 10 members) |
| DQ-13 | fraud_case | warn | 0 | 0 | Pass (no routing matrix configured) |
| DQ-14 | fraud_case | block | 100 | 0 | Pass (match rate 10.00%, minimum 0.00%) |

## Hand-checked values
| Case / check | Expected (worked by hand) | Actual |
|---|---|---|
| FC0000002 days_to_close / ratio | 3.00 / 0.8000 | 3.00 / 0.8000 |
| FC0000001 case_age_days at 2026-10-04 | 63 | 63 |
| FC0000011 (Critical, open 60 days) | SLA 30 → breached | breached |
| FC0000054 (High, open exactly 46 days) | SLA 45 → breached | breached |
| FC0000058 (High, closed in 11 days) | not breached | not breached |
| Open breaches by priority | Critical 15, High 9 (FC6..FC54), Medium 3 (FC1, FC5, FC9), Low 0 | same; 27 total |
| Closed cases breached | 0 (max 12 days to close, min SLA 30) | 0 |
| Routing matrix {Card Fraud: Card Ops} | 20 Card Fraud − 5 in Card Ops = 15 | 15 |
| account_found_flag | A0000001–A0000010 TRUE (core A00001–A00010) | 10 TRUE / 90 FALSE |

## Not covered by automated tests
- Performance at volume (the sample has only 100 rows)
- Access roles / catalog (platform tasks)
