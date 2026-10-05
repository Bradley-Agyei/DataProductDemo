# DP_Member_360 – build framework

Builds `member_360` (one row per member) from the 8 source CSVs in `data/raw/`.
Every column type comes from one place, the contracts. The parsers, DDL, DQ rules, CSV export and data contract all read them from there.

## Layout
```
contracts/
  sources.py        # 8 source tables, 60 typed columns
  member_360.py     # product (12 cols), member_id_xref, dq_exceptions
src/dp_framework/   # generic: reuse for the next data product
  contract.py       # Column / Table model + DDL generator
  types.py          # "$1,225.35 " / "($199.78)" -> Decimal, M/D/YYYY -> date, TRUE -> bool ...
  ingest.py         # raw layer: read as text, add src_file_name, src_load_ts, dp_batch_id
  standardize.py    # typed staging; bad values and duplicate keys -> rejects
  dq.py             # rule engine (block / reject / warn) + rule factories
  load.py           # SQLite: atomic replace, append-only history
  publish.py        # CSV export, data_contract.json/.md, DDL files
  ops_tables.py     # rejects, dq_results, run_log
src/member_360/     # product-specific only
  config.py         # paths, switches (Settings), age bands, US states
  transform.py      # member ID conformance, relationship status, pending attributes
  dq_rules.py       # DQ-01..DQ-10
  exceptions.py     # negative balances, dormant members active on Restricted accounts
  run.py            # pipeline + CLI
sql/ddl/            # generated from contracts (do not hand-edit)
tests/              # pytest; uses the real sample sources
```

## Run
```bash
pip install pandas pytest
python -m src.member_360.run --as-of 2026-10-04          # exit 0 = published, 1 = blocked by DQ
python -m src.member_360.run --digital-proxy             # fill digital_enrolled_flag from C03/C04 usage
python -m src.member_360.run --account-ref ../../../data/reference/account_id_map.csv
```
Account IDs: every core banking account must appear in the shared account ID mapping reference table, `data/reference/account_id_map.csv` (DQ-11 rejects any that don't). To rebuild and check that table, run these from the project root:
```bash
python -m tools.build_account_id_map && python -m tools.validate_account_id_map
```
Outputs:
- `member_360.db`: SQLite tables `raw_*`, `stg_*`, `member_360`, `member_id_xref`, `rejects`, `dq_results`, `run_log`, `dq_exceptions`
- `out/`: `member_360.csv`, `dq_exceptions.csv`, `data_contract.json`, `data_contract.md`

## Test
```bash
pytest -q
```

## Common changes
| Change | Where |
|---|---|
| A column's type or allowed values | `contracts/*.py`, then `python -m src.member_360.run --write-ddl` |
| A new feed lands (e.g. KYC) | Set the column's `status` to ready in `contracts/member_360.py` and map it in `transform.py` |
| Turn the Restricted rule or the digital proxy on or off | `Settings` in `src/member_360/config.py` |
| Add a DQ rule | `src/member_360/dq_rules.py` (use the factories in `dp_framework/dq.py`) |
| A new source system's account IDs | Add it to `SYSTEMS` in `tools/build_account_id_map.py` and rebuild the table |
| Change `dp_framework` | Change it here, copy it to every product (`test_framework_sync.py` checks the copies match) |

## Behaviour notes
- **Reruns:** each run rebuilds every table in one transaction. `rejects`, `dq_results` and `run_log` keep history, keyed by `dp_batch_id`.
- **Blocking failure:** `member_360` is not replaced, so consumers keep the last good version.
- **Pending columns** (`age_band`, `digital_enrolled_flag`, `kyc_status`, `risk_rating`, `last_profile_update_ts`): published as NULL and skipped by the NOT NULL check until their feeds are live.

Docs: the PRD, data dictionary and Jira links are in `output/DP_Member_360/`.
