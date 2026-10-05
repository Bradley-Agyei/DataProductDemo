# DP_Fraud_Case – build

Builds `fraud_case` (one row per fraud case) from the case-management extract `data/raw/DP_Fraud_Case.csv`.
It uses the same contract-driven `dp_framework` as DP_Member_360. The two copies must stay identical; `test_framework_sync.py` checks this.

## Layout
```
contracts/
  sources.py        # extract: 13 typed columns, patterns, allowed values (timestamps are ET)
  fraud_case.py     # product: 13 + 8 derived + 2 audit columns; status snapshot; dq_exceptions
src/dp_framework/   # shared framework (change it in DP_Member_360 first, then copy)
src/fraud_case/
  config.py         # paths, reference files, Settings (SLA map, match-rate minimum, routing matrix, DQ-10 severity)
  transform.py      # metrics, SLA, member/account lookups, status snapshot
  dq_rules.py       # DQ-01..DQ-14
  exceptions.py     # MEMBER_NOT_FOUND, ACCOUNT_NOT_FOUND, CASE_SLA_BREACHED
  run.py            # pipeline + CLI
sql/ddl/            # generated from contracts
tests/              # pytest; tests/data holds member_360.csv (10 members) and account_id_map.csv
```

## Run
```bash
pip install pandas pytest
# needs member_360.csv from DP_Member_360 (default path) or --member-ref,
# and data/reference/account_id_map.csv (default) or --account-ref
python -m src.fraud_case.run --as-of 2026-10-04
python -m src.fraud_case.run --member-ref tests/data/member_360.csv --account-ref tests/data/account_id_map.csv --as-of 2026-10-04
```
Outputs:
- `fraud_case.db`: `raw_fraud_case_extract`, `stg_fraud_case_extract`, `fraud_case`, `fraud_case_status_snapshot`, `rejects`, `dq_results`, `run_log`, `dq_exceptions`
- `out/`: `fraud_case.csv`, `dq_exceptions.csv`, `data_contract.json`, `data_contract.md`

## Test
```bash
pytest -q
```

## Settings (`src/fraud_case/config.py`)
| Setting | Default | Decision |
|---|---|---|
| `sla_days_by_priority` | Critical 30, High 45, Medium 60, Low 90 | Q5, pending Fraud Ops sign-off |
| `min_member_match_rate` | 0.0 (never blocks) | Q1; raise once Member 360 has the full member feed |
| `allowed_queues_by_case_type` | None (DQ-13 off) | Q4; set when Fraud Ops supplies a routing matrix |
| `confirmed_zero_loss_severity` | `warn` | Q6 |

## Common changes
| Change | Where |
|---|---|
| A type or allowed value | `contracts/*.py`, then `python -m src.fraud_case.run --write-ddl` |
| A new system's account IDs | `tools/build_account_id_map.py` (`SYSTEMS`), then rebuild the reference table |

Docs: the PRD, dictionary, stories, test report and Jira links are in `output/DP_Fraud_Case/`.
