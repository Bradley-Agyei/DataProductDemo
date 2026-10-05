# Design

## Context

- Two products were built with the same contract-driven framework:
  - `output/DP_Member_360/04_code`
  - `output/DP_Fraud_Case/04_code`
- Each product has its own byte-identical copy of `src/dp_framework/`.
- Column types live only in each product's `contracts/`. DDL is generated from them, and a test keeps the committed DDL in sync.
- Open decisions are `config.Settings` switches.
- DQ rules run through `dp_framework.dq.run_rules`. A rule has a fixed severity (block / reject / warn), and its check returns either a row mask or a failure count.
- `dq_results` has no column for a metric value.
- Fraud Case already reads Member 360's published `member_360.csv` through a configurable path. Its tests use a checked-in copy.
- For motivation see proposal.md (Why). For required behaviour see `specs/`.

## Goals / Non-Goals

**Goals:**
- Turn each of Q1–Q7 into tested behaviour or a recorded decision, without changing any published value except by adding columns or exceptions.
- Keep the two framework copies identical after the change.

**Non-Goals:**
- Getting the full member or account feeds into Member 360. That is a data delivery task; this change only makes the product ready for it.
- Time-zone-aware storage or conversion.
- Rebuilding status history before the go-live date.

## Decisions

### D1 — Account mapping is a shared reference table, not a product output
- `data/reference/account_id_map.csv` is reference data. Its columns are `source_system`, `source_account_id`, `account_id`, `in_core_banking` and `mapping_rule`, keyed by (`source_system`, `source_account_id`).
- It is built by a small generator, `tools/build_account_id_map.py`, from each system's source file, using one conversion function (`conform_account_id`: `A` + 1–7 digits → `A` + 7). It is checked by a validator covering pattern, key uniqueness and same-system collisions.
- Both products read the table through a configurable path (`--account-ref`).
  - Member 360 adds source rule **DQ-11** (reject): every core banking account must appear in the table under `core_banking`.
  - Fraud Case looks up `fraud_case_mgmt` rows to set `account_found_flag` from `in_core_banking`.
- *Why not a Member 360 output (the earlier draft):* the mapping has to cover systems Member 360 never reads (fraud case management, legacy `A0001`-style feeds). A reference table any product can read, and that a data steward can review, is the simpler owner.
- *Alternative rejected:* each product converts IDs itself. Identity logic would be duplicated and would drift.

### D2 — Match-rate gate is a separate blocking rule (DQ-14)
- **DQ-12** stays a per-row warning.
- **DQ-14** is a table-level BLOCK rule. Its check returns 0 when the rate is at or above the minimum, and otherwise the number of unmatched cases.
- The rate and the minimum are written into the DQ-14 description (e.g. `member match rate 10.00% >= minimum 0.00%`). The rate is known when product rules are built, because those rules are built after the transform.
- *Alternative rejected:* adding a `metric_value` column to `dq_results`. It's cleaner, but it changes the framework's shared ops table in both products for one number. We can revisit once a second metric appears (Rule of Three).

### D3 — SLA as a priority map; new columns go before the audit columns
- New setting: `Settings.sla_days_by_priority` (default `{Critical: 30, High: 45, Medium: 60, Low: 90}`).
- New product columns, appended after `member_found_flag` and before `dp_load_ts`: `account_found_flag BOOLEAN`, `sla_days INT`, `sla_breached_flag BOOLEAN`. The product grows from 20 to 23 columns. The sample's 13 columns stay first and in their original order.
- `CASE_SLA_BREACHED` replaces `CRITICAL_CASE_AGED`. It reports open cases only; closed breaches show in the flag but aren't actionable, so they don't become exceptions.
- `critical_sla_days` is removed from Settings.

### D4 — Time zone is metadata only
- `CONTRACT_META.timezone = "America/New_York"`, and timestamp column descriptions get an "(ET)" suffix.
- Values stay naive datetimes.
- *Alternative rejected:* timezone-aware datetimes. They need `tzdata` on Windows and would change every timestamp's text format for consumers, with no correctness gain while every source is in ET.

### D5 — Routing check: setting off by default
- New setting: `Settings.allowed_queues_by_case_type: Mapping[str, tuple[str, ...]] | None = None`.
- **DQ-13** (warn) is always registered, so `dq_results` always has the same set of rule IDs.
- With no matrix the rule must report 0 rows checked. The engine always reports the table size, so `dp_framework.dq.Rule` gains an optional `applies` predicate (added during implementation). When it returns False, the rule is recorded as Pass with 0 rows checked and the check is skipped. This is a generic, backward-compatible framework addition, covered by `tests/test_framework_dq.py` in both products.

### D6 — Status history uses a partition replace added to the framework
- New table `fraud_case_status_snapshot`:
  - columns: `snapshot_date DATE`, `case_id VARCHAR(10)`, `case_status VARCHAR(15)`, `priority VARCHAR(10)`, `assigned_queue VARCHAR(30)`, `dp_batch_id VARCHAR(36)`
  - primary key: (`snapshot_date`, `case_id`)
- New generic method: `Warehouse.replace_partition(table, df, column, value)`. In one transaction it runs CREATE IF NOT EXISTS, deletes rows where `column = value`, then inserts.
- The framework change is copied to Member 360's `dp_framework`, so both copies stay identical. A test in each product compares the framework files' hashes.
- Snapshots are written only when the run status is SUCCESS.

### D7 — Q6 recorded, no behaviour change
- DQ-10 stays a warning, and the existing `confirmed_zero_loss_severity` setting is kept. Only the docs change.

## Risks / Trade-offs

- [SLA defaults are proposals, not signed off] → They're held in a single setting. The PR and the Jira comment ask Fraud Ops to confirm them, and changing them needs no code change.
- [Renaming the exception breaks consumers that filter on `CRITICAL_CASE_AGED`] → Note it as BREAKING in the PR and on SCRUM-25. Today there is one consumer and no production deployment.
- [Fraud Case now depends on two Member 360 files] → Both paths are configurable. A missing file fails fast with its name. Tests use checked-in copies taken from a real Member 360 run.
- [The two framework copies drift apart] → A hash-equality test in each product.
- [Rate stored in a description string is awkward to query] → Accepted for now (see D2).

## Migration Plan

1. Add the reference table generator and validator. Implement the Member 360 DQ-11 check and run its tests, then commit them on top of `feature/SCRUM-17-member-360`.
2. Copy `account_id_map.csv` into the Fraud Case test data.
3. Implement the Fraud Case changes. Run its tests, then commit them on top of `feature/SCRUM-25-fraud-case`.
4. Merge order: SCRUM-17 before SCRUM-25 (the runtime dependency is on Member 360's outputs).
5. **Rollback:** revert the follow-up commit on either branch. The snapshot table is additive and can be dropped.
