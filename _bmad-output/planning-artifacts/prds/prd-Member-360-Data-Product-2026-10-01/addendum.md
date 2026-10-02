# Addendum — Member 360 Data Product

Companion to `prd.md`. Holds detail that is **technical-how** or **rejected-alternative rationale** — material that belongs to the downstream architecture workflow rather than the PRD's requirements narrative. Nothing here is a requirement; the PRD is authoritative.

---

## A1. Proposed target schema (26 columns)

Indicative, not contractual — the PRD states capabilities, this states a concrete shape the architect can react to. Types are suggestions.

### Identity and profile — carried from source (10)

| Column | Type | Notes |
|---|---|---|
| `member_id` | string | PK. Format unresolved — Open Question 1. |
| `member_since_date` | date | |
| `member_segment` | string | Retail / Premium / Student / Small Business. Primary reporting dimension. |
| `age_band` | string | Coarsened in place of date of birth. |
| `home_state` | string | Coarsened in place of postal code. |
| `digital_enrolled_flag` | boolean | Pairs with `digital_txn_count_30d` for the UJ-2 insight. |
| `kyc_status` | string | Verified / Review Required. |
| `risk_rating` | string | Low / Medium / High. |
| `relationship_status` | string | Source-declared. **Not** `activity_status`. |
| `last_profile_update_ts` | timestamp | |

### Account rollup — derived (2)

| Column | Type | Notes |
|---|---|---|
| `open_account_count` | int | Open accounts only. Zero, never null. |
| `total_current_balance` | decimal(18,2) | Sum across open accounts. Source arrives as formatted string. |

### Activity measures — derived, Member-Initiated only (9)

All nine count **Member-Initiated Transactions**: Posted status, excluding Transaction Category `Interest` / `Fee` and Channel Group `System`. In the sample extracts that excludes `TT09`, `TT10`, `C09`, `C10`.

| Column | Type | Notes |
|---|---|---|
| `txn_count_30d` | int | Zero, never null. |
| `txn_amount_30d` | decimal(18,2) | |
| `txn_count_prior_30d` | int | Days 31–60 back from As-Of Date. Disjoint from the 30d window. |
| `txn_amount_prior_30d` | decimal(18,2) | |
| `txn_count_lifetime` | int | |
| `txn_amount_lifetime` | decimal(18,2) | |
| `digital_txn_count_30d` | int | Channel Group = Digital. Pairs with `digital_enrolled_flag` for the UJ-2 insight. |
| `primary_channel_group` | string | Modal channel group over 30d. Null if no 30d activity. |
| `primary_txn_category` | string | Modal category over 30d. Null if no 30d activity. |

**No `txn_count_change_pct` column.** Deliberately omitted — the analyst holds both counts and the BI layer divides. A stored ratio is a third thing that can disagree with the two columns it came from, and it buys nothing a dashboard cannot compute for free.

**Implementation note.** The prior-window measures are the *same* aggregation with a shifted date predicate, not new logic. Expect a single pass computing both windows via conditional aggregation rather than two scans of the transaction set.

### Recency and derived status (3)

| Column | Type | Notes |
|---|---|---|
| `last_txn_date` | date | Null only if never transacted. |
| `days_since_last_txn` | int | Null when `last_txn_date` is null. |
| `activity_status` | string | Active / Lapsing / **Inactive**. Never null. Derived; thresholds unconfirmed. `Dormant` deliberately avoided — it is a regulated term under state unclaimed-property law with a multi-year clock. |

### Freshness and lineage (2)

| Column | Type | Notes |
|---|---|---|
| `as_of_date` | date | Identical across all rows in a run. The UJ-3 field. |
| `dp_load_ts` | timestamp | Run completion time. |

---

## A2. Grain decision — options considered

**Chosen: wide table, one row per Member.**

| Option | For | Against |
|---|---|---|
| **A. Wide table, one row per Member** *(chosen)* | Single-query sufficiency; no double-count risk; trivially understood by one analyst; each new time window is an additive, reversible column change | No history; each new window widens the table; sprawl risk over time (hence counter-metric SM-C1) |
| **B. Daily snapshot, one row per Member per day** | Any time window computable by the consumer; history free; survives questions not yet asked | An unfiltered `SUM` over the snapshot table is silently wrong by a factor of N days — a realistic failure that reaches a board pack; more storage; more explaining |
| **C. Dimension table + separate activity fact** | Clean modeling; normalized | Makes the analyst perform the join, which means the product is not finished. Rejected on the grounds that a data product requiring a join to answer its own headline metric is a schema, not a product |

**Rationale for A over B.** The deciding argument was reversibility against a concrete scope. One analyst, one dashboard, two known questions. B optimizes for query patterns nobody has requested, at the cost of a specific and well-documented footgun. A's failure mode — "we need another window" — is a two-line additive change; B's failure mode is a wrong number nobody catches. Chose the reversible failure.

**The cost of that choice, stated plainly.** Option A has no history, which means period-over-period trend is not computable from the product. This was not fully priced when the decision was taken — Option B's strongest argument turns out to be trend, not flexibility. **Resolved in A3** by carrying prior-window measures on the same row rather than by reopening the grain: that recovers the single comparison the headline metric needs while keeping everything option A was chosen for. A multi-period trend chart remains out of reach and would require revisiting this decision.

---

## A3. Trend capability — options considered (PRD Open Question 3, RESOLVED)

**Chosen: option 2 — Prior 30-Day Window measures carried on the existing row.**

The problem: the product is one row per Member, overwritten each run, so it has no memory. "Member activity by segment" reads naturally as a trend, and a current-state-only table cannot produce one. This surfaced *after* the grain decision in A2 was taken, and it is the strongest argument the snapshot position had.

| Option | Headline "down 12%" | Trend line | Per-member history | Cost | New artifact |
|---|---|---|---|---|---|
| 1. Accept current-state only | ✗ | ✗ | ✗ | none | no |
| **2. Prior-period columns** *(chosen)* | **✓** | ✗ | ✗ | ~1 hr | no |
| 3a. Segment-grain daily history | ✓ | ✓ | ✗ | ~half day | yes |
| 3b. Member-grain daily history | ✓ | ✓ | ✓ | ~half day | yes |
| 4. Snapshot grain + current view | ✓ | ✓ | ✓ | ~1 day | view |
| 5. Delta time travel | partial | ✗ | ✗ | none | no |

**Why option 2.** It produces the exact sentence the stakeholder will say out loud — *"Premium activity is down 12%"* — with no new table, no grain change, and no new failure mode. It reuses the aggregation already being written, parameterized on a shifted date predicate. And at Member grain it does something the other cheap options cannot: holding both windows on one row turns UJ-2 from *who is quiet* into *who went quiet*, which is a materially better retention list because it excludes members who were never active.

**What it costs.** One comparison, not a time series. No multi-period line chart. Accepted and documented (PRD §6.2), not overlooked.

**Why not the others.**
- **Option 1** is free and honest, and does not survive the first follow-up question in a meeting.
- **Options 3a / 3b** are the real trend answer and remain the designated next step if a line chart is required. 3a is roughly four rows per day. Nothing built for v1 is wasted by adding it later — which is precisely what makes option 2 safe to choose now.
- **Option 4** is the most architecturally correct, and the most *instructive* if the goal is to demonstrate production-grade practice: the `_Current` view neutralizes the snapshot double-count footgun while retaining full history. Rejected for v1 on scope, not on merit. Worth revisiting if this demo is ever extended to show a complete pattern end to end.
- **Option 5 should not be the primary mechanism.** Delta time travel looks attractive and is weak in practice for dashboards: version retention is finite and short by default, versions map to pipeline runs rather than business dates (so any re-run breaks the correspondence), and BI tools cannot cleanly parameterize `VERSION AS OF`. Legitimate for ad-hoc forensics; not a reporting foundation.

---

## A4. Pipeline shape (indicative)

Layered, in the conventional progression. Named to orient the architect, not to constrain them.

1. **Land** — the eight extracts, unmodified, partitioned by ingest date. Preserves the ability to reproduce any run and makes a source-side schema change fail at a known boundary (PRD FR-1).
2. **Conform** — type casting (currency strings → decimal, mixed date formats → date), `member_id` normalization, dimension joins to attach `channel_group` and `transaction_category` to each transaction. This is where most defects will live.
3. **Aggregate** — transaction rollups per member across both windows; account rollups per member; derivation of recency fields and `activity_status`.
4. **Validate** — the five FR-12 checks, as a gate. Fail here and step 5 does not run.
5. **Publish** — atomic overwrite of `DP_Member_360` in Unity Catalog, with table/column comments applied as part of the write rather than as a manual afterthought.

**Idempotency mechanism.** Full recompute for the As-Of Date and atomic replace, rather than incremental merge. At this data scale incremental buys nothing and introduces exactly the state-dependence that breaks re-runnability. The Posted-only rule (PRD FR-6) is what makes full recompute correct across the Pending → Posted transition: a transaction simply does not exist to the pipeline until it is Posted, so no reconciliation or reversal logic is needed.

Concretely: `INSERT OVERWRITE` (or `replaceWhere` scoped to the batch date) is the standard idempotent Delta write. Plain `INSERT INTO` is **not** idempotent and is the single most common way this requirement gets silently violated. Should the pipeline ever become incremental, Delta's `txnAppId` + `txnVersion` options dedupe duplicate writes at the transaction-log level and become the mechanism of record for FR-2.

**On the Pending → Posted model.** The prevailing industry pattern (Plaid's is the widely referenced one) is that posting creates a **new** transaction id carrying a pointer back to the pending one, rather than updating the pending row in place. The sample extracts show no such pointer, so the Posted-only rule is the right call here. If the real feed turns out to carry both rows with a linkage field, the alternative — keep both, suppress any pending row referenced by a posted row — becomes available and slightly more accurate. Worth checking the real feed shape before build.

**Tie-break determinism** (PRD FR-8). `primary_channel_group` on a tie must resolve the same way every run — e.g. highest count, then alphabetically first channel group. Without an explicit rule the value flickers between runs and the table fails its own idempotency requirement.

---

## A5. Observations on the sample data

Noted during discovery; relevant to build, not requirements.

- **Row counts don't reconcile.** `data/raw/Member.csv` has 10 rows, `data/product/DP_Member_360.csv` has 100. The sample product was authored independently of the sample sources. Fine for a demo; means the sample product file cannot be used as an expected-output fixture for testing without regenerating it.
- **`member_id` format differs** between raw (`M0001`) and product (`M000001`) — PRD Open Question 1.
- **Monetary values arrive as formatted strings** with currency symbols, thousands separators, and trailing spaces (`"$1,337.72 "`). Parsing is required before any arithmetic; a naive cast will null them silently.
- **Dates arrive in `M/D/YYYY`**, while `Transaction.csv` uses a `date_key` integer (`20260921`) joining to `Date.csv`. Two date representations to reconcile at conform.
- **The dimension tables are better than they look.** `Channel.channel_group` (Assisted / Self-Service / Digital / External / System) and `Transaction_Type.transaction_category` (Funding / Cash / ACH / Card / Wire / Fee / Interest) are already clean analytical rollups. Carrying them through costs one join each and removes the need for the analyst to maintain her own lookup — this is the single highest value-per-effort item in the build.
- **`Transaction.csv` contains `Pending` rows**, which is what motivated the Posted-only rule rather than it being theoretical.
- **`Transaction.csv` also contains institution-generated rows.** `TT09` (Fee) and `TT10` (Interest) are not member actions, and `C09` (Batch Processing) / `C10` (API) are System channels. This is what motivated the Member-Initiated rule — again, observed rather than hypothetical.

---

## A6. Research findings behind the requirements

Conventions checked during discovery. Recorded so a reviewer can see which requirements are grounded and which are still guesses.

**Activity and dormancy definitions.** There is **no single industry standard** for "active member" — this was checked and the absence is the finding. What is real: ~90 days with no member-initiated transaction is a common operational inactivity threshold, while credit union member-facing policies more often use 12 months before inactivity treatment. **Dormancy is genuinely regulated**, but by *state* unclaimed-property law rather than federal rule — the Uniform Unclaimed Property Act sets 3 years of no owner-initiated activity before escheatment for checking and savings, with states ranging 3–5 years. Crucially, "owner-initiated" explicitly excludes interest postings and institution-generated entries. That exclusion is the defensible, citable part, and it is why the Member-Initiated rule exists in FR-6 rather than being a stylistic preference. It is also why `activity_status` does not use the value `Dormant`.

**Credit union measurement precedent.** Engagement is conventionally measured per *member* rather than per account (NCUA 5300 Call Report counts members; Callahan's relationship/penetration ratios build on that). This is independent support for the one-row-per-member grain chosen in A2.

**Unity Catalog conventions.** Three-level `catalog.schema.table`, lowercase snake_case, with the medallion layer expressed in catalog or schema rather than a table prefix — `prod.gold.member_360` would be idiomatic where `DP_Member_360` is not. Certification is a real platform feature, not a documentation convention: a governed tag renders a certification mark in Catalog Explorer, which is why FR-10 requires it. Delta capabilities worth naming as requirements rather than delegating: schema enforcement on write, time travel and `RESTORE` for rollback (30-day default retention), `MERGE` for upserts, and `OPTIMIZE` / Z-ORDER or liquid clustering keyed on `member_id`.

**Data quality framework.** The six dimensions in FR-12 are DAMA UK / DMBOK — completeness, uniqueness, timeliness, validity, accuracy, consistency. Using the standard names matters: it lets a client governance function map our checks onto their existing framework without translation. Accuracy is the one dimension that cannot be fully automated; a reconciliation tolerance against source is the conventional proxy, which is what FR-12 specifies.

**Privacy regime.** GLBA is correct for a US credit union, implemented through NCUA Regulation P with the safeguards program under NCUA Part 748 / Appendix A. Account balances and transaction history are explicitly NPI. **GLBA has no de-identification safe harbor** — this is the finding that forced the pseudonymized/anonymized distinction in PRD §10. Teams conventionally borrow HIPAA Safe Harbor as a recognizable yardstick (drop names and addresses, geography no finer than state, ages banded with 90+ collapsed), which is exactly the shape of the existing product schema. Borrowing the pattern confers no legal status, and the PRD says so.

*Sources consulted: Uniform Unclaimed Property Act / state escheatment guidance; NCUA 5300 Call Report instructions; NCUA Regulation P and Part 748; Databricks Unity Catalog governed tags, naming, and idempotent-writes documentation; Delta Lake batch documentation; Plaid transactions pending/posted model; DAMA UK six data quality dimensions; HHS de-identification guidance.*
