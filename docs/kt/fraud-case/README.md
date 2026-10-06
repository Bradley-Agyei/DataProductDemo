# Fraud Case data product: knowledge transfer

## What this is

Fraud cases live in a case-management system. Analysts export them by hand, and each team works out losses and case age its own way. `DP_Fraud_Case` (Jira SCRUM-25) turns that extract into one governed, typed row per case, with lifecycle checks, loss metrics, an SLA by priority, and links to Member 360 and to core banking accounts.

It is the second product built on `dp_framework`, a small contract-driven pipeline framework shared with `DP_Member_360` (SCRUM-17). Both live under `output/`, and each carries its own byte-identical copy of the framework.

| Piece | What it does | Start here |
|---|---|---|
| `output/DP_Fraud_Case/` | `fraud_case`, one row per case, plus a daily status snapshot | `PRD_Fraud_Case.md`, `04_code/README.md` |
| `output/DP_Member_360/` | `member_360`, one row per member, from the 8 extracts in `data/raw/` | `PRD_Member_360.md`, `04_code/README.md` |
| `src/dp_framework/` (in both) | ingest, standardize, DQ engine, SQLite load, publish | the module docstrings |
| `tools/build_account_id_map.py` | builds the shared account ID mapping table (SCRUM-32) | its docstring |
| `data/reference/account_id_map.csv` | maps each system's account ID to canonical `A` + 7 digits | PRD section 5.3 |

## Why it looks the way it does

The first build shipped with seven open questions (PRD section 11, Q1 to Q7). The OpenSpec change `openspec/changes/resolve-fraud-case-open-decisions` decided each one, and every decision is now either a `Settings` switch or tested behaviour:

| Question | Decision | Where it lives |
|---|---|---|
| Q1 Member coverage | Keep and flag unmatched members. DQ-14 records the match rate and blocks below a minimum, default 0 (never blocks). | `Settings.min_member_match_rate` |
| Q2 Account IDs | Canonical `A` + 7 digits, via the shared reference table. `account_found_flag` and an `ACCOUNT_NOT_FOUND` exception. | `tools/`, `data/reference/` |
| Q3 Time zone | US Eastern, stored without an offset. Declared in the data contract only; no values change. | `CONTRACT_META["timezone"]` |
| Q4 Routing | Not enforced. DQ-13 warns, but only once a routing matrix is configured. | `Settings.allowed_queues_by_case_type` |
| Q5 SLA | Critical 30, High 45, Medium 60, Low 90 days. Pending Fraud Ops sign-off. | `Settings.sla_days_by_priority` |
| Q6 $0 Confirmed Fraud | Stays a warning (DQ-10): fully recovered funds can leave a $0 loss. | `Settings.confirmed_zero_loss_severity` |
| Q7 Status history | `fraud_case_status_snapshot`, one row per case per run date, from go-live. | `contracts/fraud_case.py` |

The design rationale, including the alternatives that were rejected, is in that change's `design.md` (D1 to D7).

## How a run works

`src/fraud_case/run.py` is the whole pipeline, in order:

1. **Ingest.** Read the extract as text, check the header, and stamp the file name, load time and batch ID.
2. **Standardize.** Cast every column to its contract type. Bad values and duplicate `case_id`s go to `rejects`.
3. **Source DQ** (DQ-06 to DQ-11). Lifecycle and loss rules. Reject rules remove the row and log the rule ID.
4. **Derive.** `is_closed`, `days_to_close`, `case_age_days`, `loss_confirmation_ratio`, the member and account flags, `sla_days`, `sla_breached_flag`.
5. **Product DQ** (DQ-01 to DQ-05, DQ-12 to DQ-14). Any failing block rule makes the run `BLOCKED`.
6. **Load and publish.** On `SUCCESS` only: replace `fraud_case`, write that date's snapshot partition, and write `out/`.

Exit code 0 means published, 1 means blocked.

## Setup, once

There is no requirements file. The suites need `pandas` and `pytest` only. Use a virtualenv outside the repo, and put its interpreter first on your `PATH` so `python` below means the venv:

```bash
python -m venv <venv-dir>
```

```bash
python -m pip install -q pandas pytest
```

Verified with Python 3.14.4, pandas 3.0.6 and pytest 9.1.1. No versions are pinned anywhere in the repo.

## Run the tests

Each product's `pytest.ini` sets `pythonpath = .`, so run pytest from inside its `04_code/`:

```bash
cd output/DP_Member_360/04_code && python -m pytest -q
```

```bash
cd output/DP_Fraud_Case/04_code && python -m pytest -q
```

From the project root, the account ID tools and the repo's own gate tests:

```bash
python -m pytest -q tools/tests
```

```bash
python -m unittest discover -s tests -t .
```

Expect 109, 106 and 21 passed for the three pytest runs, and 29 tests OK for `unittest`.

## Run the pipelines

From `output/DP_Fraud_Case/04_code`, against the checked-in test references (no Member 360 build needed):

```bash
python -m src.fraud_case.run --member-ref tests/data/member_360.csv --account-ref tests/data/account_id_map.csv --as-of 2026-10-04
```

Or with the defaults, which read Member 360's published `out/member_360.csv`, so build that first from `output/DP_Member_360/04_code`:

```bash
python -m src.member_360.run --as-of 2026-10-04
```

```bash
python -m src.fraud_case.run --as-of 2026-10-04
```

After changing a contract, regenerate the DDL:

```bash
python -m src.fraud_case.run --write-ddl
```

After changing a source system's account IDs, from the project root:

```bash
python -m tools.build_account_id_map --check
```

```bash
python -m tools.validate_account_id_map
```

Drop `--check` to rewrite `data/reference/account_id_map.csv`.

## Where things live

| Change | Where |
|---|---|
| A column's type, pattern or allowed values | `contracts/sources.py` or `contracts/fraud_case.py`, then `--write-ddl` |
| A business switch (SLA, match-rate minimum, routing, DQ-10 severity) | `Settings` in `src/fraud_case/config.py` |
| A DQ rule | `src/fraud_case/dq_rules.py`, using the factories in `dp_framework/dq.py` |
| An exception type | `src/fraud_case/exceptions.py` |
| A new system's account IDs | `SYSTEMS` in `tools/build_account_id_map.py`, then rebuild the table |
| The framework | `src/dp_framework/` in Member 360 first, then copy it to Fraud Case |

Run outputs, all gitignored: `fraud_case.db` (SQLite) and `out/` (`fraud_case.csv`, `dq_exceptions.csv`, `data_contract.json`, `data_contract.md`).

## Gotchas

- **The extract is read from `data/product/`, not `data/raw/`.** `data/raw/` is read-only and stands in for upstream feeds, so the copy this PR first put there was removed. `config.SOURCE_DIR` and the fraud row in `tools/build_account_id_map.py` now point at `data/product/DP_Fraud_Case.csv`, which was byte-identical. Some prose (the PRD, `04_code/README.md`, `output/README.md`) still says `data/raw/`.
- **Run Member 360 first, or pass `--member-ref`.** A missing reference file fails the run before anything is published, naming the file.
- **The test references are copies.** `tests/data/account_id_map.csv` is the same blob as `data/reference/account_id_map.csv`; `tests/data/member_360.csv` is a 10-member Member 360 build. Rebuild the reference table and the copy goes stale silently.
- **`dp_framework` is duplicated on purpose.** `tests/test_framework_sync.py` fails when the two copies differ, but skips when the sibling product is not checked out, so a lone product folder proves nothing.
- **`--as-of` defaults to today.** `case_age_days`, `sla_breached_flag` and the `CASE_SLA_BREACHED` count move every day. Tests pin 2026-10-04; pass `--as-of` when comparing runs.
- **BREAKING for consumers.** `CASE_SLA_BREACHED` (all priorities, open cases only) replaced `CRITICAL_CASE_AGED`, and `fraud_case` grew from 20 to 23 columns, added before the audit columns.
- **A blocked run still writes history.** `rejects`, `dq_results` and `run_log` are appended and `dq_exceptions` is replaced, but `fraud_case`, the snapshot and `out/` keep the last good version.
- **DQ-14's match rate is only in its description string.** `dq_results` has no metric column (design D2), so query the text.
- **SLA defaults are proposals.** They await Fraud Ops sign-off and change in `Settings` with no code change.
- **No PII.** The products carry pseudonymous IDs only. `data/raw/Member.csv` has name and postal code columns; never copy them out, and `checks.py pii` fails any tracked CSV outside `data/raw/` whose header names them.
