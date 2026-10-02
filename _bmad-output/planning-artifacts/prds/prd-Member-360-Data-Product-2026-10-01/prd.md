---
title: Member 360 Data Product
status: draft
created: 2026-10-01
updated: 2026-10-01
---

# PRD: Member 360 Data Product
*Working title — confirm.*

## 0. Document Purpose

This PRD defines the **Member 360 Data Product** — a single governed table, `DP_Member_360`, published to the client's Unity Catalog and consumed by a data analyst to build a member activity dashboard. It is written for the engineer who will build the pipeline, the architect who will review it, and the product owner who will accept it.

Structure: vocabulary is anchored in §3 Glossary and used verbatim throughout; features in §4 carry nested, globally numbered Functional Requirements (FR-N); inferences I made without confirmation are tagged `[ASSUMPTION]` inline and indexed in §9. Prior input is the discovery session captured in `.memlog.md` alongside this document, plus direct inspection of the sample extracts in `{project-root}/data/`. Technology selection and pipeline design are **out of scope for this document** — they belong to the downstream architecture workflow.

---

## 1. Vision

A credit union runs its business on eight separate microservices. Member records live in one, accounts in another, transactions in a third, and the reference data that makes any of it legible — channels, branches, products, transaction types — is scattered across five more. Any question that spans those boundaries is currently a join an analyst has to construct by hand, correctly, every single time, from sources they do not own and cannot validate.

The Member 360 Data Product collapses that work into one table. It answers a single question well — **how active are our members, cut by segment** — and it answers the obvious follow-up: *which members went quiet, and were they ever reachable digitally?* One row per member, refreshed daily, carrying both who the member is and what they actually did. No joins. No tribal knowledge about which `channel_id` means mobile.

The value is not that the data becomes available; it is already available. The value is that it becomes **trustworthy and immediate**. An analyst who can go from question to chart in one query, against a table whose freshness and quality are stated contractually rather than hoped for, asks more questions. That is the product.

---

## 2. Target User

### 2.1 Jobs To Be Done

- **Functional** — Report member activity broken out by segment, on a recurring cadence, without rebuilding a multi-table join each time.
- **Functional** — Identify members whose activity has dropped off, so retention effort can be targeted rather than sprayed.
- **Functional** — Cross member *attributes* (segment, digital enrollment, tenure) against member *behavior* in a single pass — the two have never been co-located before.
- **Contextual** — Produce a number that will be quoted in a meeting, and be able to defend where it came from and how current it is.
- **Emotional** — Stop being the bottleneck. Answer the follow-up question in the meeting, not in a ticket filed after it.

### 2.2 Non-Users (v1)

- **Branch and front-line staff** — this is an analytical table, not an operational member lookup. It carries no names and cannot identify an individual at the teller window, by design.
- **Member-facing applications** — no application reads from this product. It is a reporting asset.
- **Data scientists building models** — the activity measures here are a reasonable starting point but this is not a feature store; no point-in-time correctness guarantee is offered (see §5).
- **Executives consuming the dashboard** — they are users of the analyst's *output*, not of this product. Their needs shape the dashboard, not the table.

### 2.3 Key User Journeys

- **UJ-1. Renata builds the segment activity view and is done before lunch.**
  > Renata, the credit union's sole data analyst, has been asked for "a view of how active our members are by segment, refreshed weekly." Previously this meant requesting a transaction extract, waiting two days, and joining it to a member list in Power BI with a lookup table she maintains herself. Today she opens her SQL editor against Unity Catalog, finds `DP_Member_360` in the catalog browser, and reads the table comment — one row per member, as of yesterday's close, activity counted on posted transactions. She writes one `GROUP BY member_segment`, gets counts and 30-day transaction volume per segment, and has a chart in under thirty minutes. **Value lands** when she notices she never had to ask anyone what `C04` means — `primary_channel_group` already says "Digital."

- **UJ-2. Renata chases the drop.**
  > Her chart shows Premium transaction count down roughly 12% against the prior period, and someone will ask why. She filters the same table to `member_segment = 'Premium' AND txn_count_prior_30d > 0 AND txn_count_30d = 0` — members who *were* transacting and have stopped — and sorts by `days_since_last_txn`. That is a different and much better list than "everyone who is currently inactive," because it excludes members who were never active to begin with. She adds `digital_enrolled_flag` and `digital_txn_count_30d` and finds the sharper story: a cluster of the drop-offs are *enrolled* in digital but have zero digital transactions. That is an onboarding failure, not churn, and it is actionable this week. **Value lands** at the second query, not the first — the product survived the follow-up question.

- **UJ-3. Renata checks whether she can trust today's number.**
  > It is 8:15am and a figure from this dashboard is going into a board pack at 10. Before she sends it, Renata selects `as_of_date` and `dp_load_ts` from the table. `as_of_date` is yesterday; `dp_load_ts` is 05:47 this morning. The data is current and she sends it. **Edge case:** had `as_of_date` been two days stale, the same check would have caught it in seconds, and she would have flagged the number as provisional rather than discovering the problem after it was quoted. This journey is the one that decides whether the product gets used at all.

---

## 3. Glossary

Downstream workflows and readers must use these terms exactly. Introducing a synonym anywhere in this PRD is a discipline violation.

- **Member** — A person holding a relationship with the credit union. Identified by `member_id`. One Member may hold many Accounts. The unit of grain for this product: exactly one row per Member.
- **Account** — A financial account (Checking, Savings, Loan, etc.) belonging to exactly one Member. Many Accounts per Member.
- **Transaction** — A single posted or pending movement of funds against one Account. The sole fact source for all activity measurement.
- **Posted Transaction** — A Transaction whose `transaction_status` is `Posted`. **All activity measures in this product count Posted Transactions only.** Pending transactions are excluded because they mutate between daily runs.
- **Member-Initiated Transaction** — A Posted Transaction the Member caused, as opposed to one the institution generated. Excludes interest postings, fee assessments, and anything arriving on the `System` Channel Group. **This is the basis of all activity measurement in this product** — an interest credit is not evidence that a Member is engaged, and counting it inflates every activity measure. The member-initiated distinction is also the one that carries weight in unclaimed-property law, which is why it is drawn here rather than left implicit.
- **Source Extract** — One of the eight upstream files standing in for a microservice feed: Member, Account, Transaction, Product, Branch, Channel, Transaction_Type, Date.
- **Data Product** — The published table `DP_Member_360` and its accompanying contract (schema, freshness guarantee, quality checks). The deliverable in its entirety.
- **Member Segment** — The commercial classification of a Member: Retail, Premium, Student, Small Business. Sourced, not derived. The primary reporting dimension.
- **Relationship Status** — The Member's status **as declared by the source system**: Active, Dormant, Restricted. Sourced, not derived.
- **Activity Status** — The Member's status **as derived from observed Member-Initiated Transactions**: `Active`, `Lapsing`, `Inactive`. Computed by this pipeline. **Deliberately distinct from Relationship Status**, and the two may disagree — a Member whose Relationship Status is Active but whose Activity Status is Inactive is a finding, not an error. **The value `Dormant` is deliberately not used here**: in US unclaimed-property law dormancy is a regulated state with escheatment consequences and a multi-year clock, and reusing the word for a 90-day analytical cut would put a term with legal meaning on a dashboard where it means something else entirely.
- **Channel Group** — The delivery-channel rollup carried from the Channel Source Extract: Assisted, Self-Service, Digital, External, System.
- **Transaction Category** — The transaction-type rollup carried from the Transaction_Type Source Extract: Funding, Cash, ACH, Card, Wire, Fee, Interest.
- **As-Of Date** — The business date through which all measures in a row are computed. Every row in a given run carries the same As-Of Date.
- **30-Day Window** — Member-Initiated Transactions where posting date falls within the 30 calendar days ending on the As-Of Date, inclusive.
- **Prior 30-Day Window** — The 30 calendar days immediately preceding the 30-Day Window — days 31 through 60 back from the As-Of Date. Exists so the product can express change without retaining history; the two windows never overlap.
- **Lifetime Window** — All Member-Initiated Transactions on or before the As-Of Date, with no lower bound.
- **Daily Run** — One complete execution of the pipeline: ingest, conform, aggregate, validate, publish.

---

## 4. Features

### 4.1 Source Ingestion

**Description:** The pipeline reads all eight Source Extracts on each Daily Run and lands them without transformation. Separating ingestion from transformation means a source-side change (a renamed column, a late file) fails loudly at a known boundary instead of corrupting a measure three steps downstream. The Daily Run must be safe to re-run — operators will re-run it, whether because of a failure, a late source file, or a mistake.

**Functional Requirements:**

#### FR-1: Ingest all source extracts

The pipeline ingests the eight Source Extracts on each Daily Run, preserving source column names and values as received.

**Consequences (testable):**
- All eight Source Extracts are read; a missing or unreadable extract fails the Daily Run with the extract name in the error.
- Source column names and values are preserved exactly as received — no renaming, casting, or cleansing at this stage.
- Monetary values arriving as formatted strings (`"$1,337.72 "`) and dates arriving in mixed formats are parsed at conformance (FR-3), not at ingestion.

#### FR-2: Daily Run is idempotent

Re-running the pipeline for the same As-Of Date produces an identical published table.

**Consequences (testable):**
- Running the pipeline twice for the same As-Of Date yields byte-identical measure values and the same row count.
- A re-run replaces the prior result for that As-Of Date rather than appending to it.
- A Transaction that was Pending on one Daily Run and Posted on the next is counted exactly once — on the run where it is first observed as Posted. *(Guaranteed by the Posted-only rule in FR-6, stated here because idempotency is where it would otherwise break.)*
- Late-arriving and corrected source rows within a defined lookback period are picked up by the next Daily Run without manual intervention. `[ASSUMPTION]` A full recompute of the Lifetime Window on every run makes this automatic and removes the need to tune a lookback figure — the conventional 3–7 day reprocess window exists for incremental pipelines, which this is not. If the data volume later makes full recompute impractical, an explicit lookback becomes a requirement rather than an implementation detail.

---

### 4.2 Member Profile Conformance

**Description:** Source Member and Account records are conformed into the pseudonymized profile attributes the product publishes. The product deliberately **omits** direct identifiers present in the source — first name, last name, postal code — and substitutes coarsened equivalents (age band, home state). This is a governance control, not an oversight, and it is what keeps the table grantable to an analyst role without per-request PII review. It does **not** make the table anonymous: `member_id` is still a key back to an identified person. See §10 Data Governance.

Account-level detail is rolled up to the Member. The analyst never sees an individual account; they see how many the Member holds and their combined balance.

**Functional Requirements:**

#### FR-3: Conform Member identity

Every Member row in the product resolves to exactly one Member in the Member Source Extract, via a single documented `member_id` format.

**Consequences (testable):**
- `member_id` is unique across the published table — zero duplicates.
- Every published `member_id` exists in the Member Source Extract; zero orphans.
- The `member_id` format is documented in the table metadata and is stable across Daily Runs.
- `[ASSUMPTION]` The canonical format is the zero-padded six-digit form `M000001`. The sample extracts are inconsistent — `data/raw/Member.csv` uses `M0001` while `data/product/DP_Member_360.csv` uses `M000001` — which means the sample product file was not generated from the sample raw files. This must be resolved before build; see §8 Open Question 1.

#### FR-4: Publish pseudonymized profile attributes

The product carries Member profile attributes with direct identifiers removed.

**Consequences (testable):**
- The published table contains no `first_name`, `last_name`, `postal_code`, account number, or free-text field capable of carrying an identifier.
- `age_band` and `home_state` are present in place of date of birth and postal code.
- `member_segment`, `kyc_status`, `risk_rating`, `relationship_status`, `digital_enrolled_flag`, `member_since_date`, and `last_profile_update_ts` are carried from source without transformation beyond type casting.

#### FR-5: Roll up Accounts to the Member

Account holdings are summarized to one row per Member.

**Consequences (testable):**
- `open_account_count` equals the count of that Member's Accounts with `account_status = 'Open'`.
- `total_current_balance` equals the sum of `current_balance` across that Member's open Accounts, as a typed decimal rather than a formatted string.
- A Member with zero open Accounts publishes `open_account_count = 0` and `total_current_balance = 0`, not null.

---

### 4.3 Activity Aggregation

**Description:** The heart of the product and the reason it exists. Member-Initiated Transactions are aggregated to the Member across two windows — 30-Day and Lifetime — and enriched with the Channel Group and Transaction Category rollups carried from the dimension extracts. Those two rollups are nearly free to compute and they are the difference between a dashboard with one chart and one with four: without `channel_group` on the row, "digital activity by segment" is a three-table join the analyst has to get right herself.

The member-initiated filter is the single most consequential definition in this document. A Member who has done nothing for six months still accrues an interest credit every month and still gets charged a maintenance fee; counting those as activity would show that Member as perfectly engaged. Every activity measure here therefore excludes institution-generated entries, and because that makes the headline number *lower* than a naive count, the rule is stated in the table's own metadata (FR-11) so nobody reconciles against a raw transaction count and concludes the pipeline is broken.

The Prior 30-Day Window exists to solve a specific problem: the product holds one row per Member and is overwritten each run, so it has no memory. Without it, "member activity by segment" could only ever be a point-in-time number, and the question that always follows — *compared to what?* — would be unanswerable. Carrying the prior window's measures on the same row buys the comparison without a second table, a grain change, or any retained history. It is a deliberate 80% solution: it yields **one** comparison, not a time series. A trend chart over many periods remains out of scope (§6.2).

Its second effect is the more useful one. Holding both windows at Member grain turns UJ-2 from *who is quiet* into *who went quiet* — a Member with activity in the prior window and none in the current one is a far better retention target than one who has simply always been inactive.

Recency fields and a derived Activity Status make UJ-2 a filter rather than an analysis.

**Functional Requirements:**

#### FR-6: Compute windowed activity measures

Member-Initiated Transaction counts and amounts are aggregated per Member over the 30-Day, Prior 30-Day, and Lifetime Windows. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- `txn_count_30d`, `txn_amount_30d`, `txn_count_prior_30d`, `txn_amount_prior_30d`, `txn_count_lifetime`, `txn_amount_lifetime` are computed from Member-Initiated Transactions only. A Transaction contributes to none of them if its status is anything other than `Posted`, **or** if it is institution-generated.
- The Prior 30-Day measures use identical logic to the 30-Day measures with the window shifted back 30 days. The two windows are disjoint — no Transaction contributes to both.
- A Member with no qualifying Transactions in the Prior 30-Day Window publishes `0`, not null.
- **No percentage-change column is published.** The analyst holds both counts and the BI layer computes the ratio. A stored percentage can disagree with the columns it was derived from after a partial refresh; a computed one cannot.
- Institution-generated is defined as: Transaction Category of `Interest` or `Fee`, or Channel Group of `System`. In the sample extracts that excludes transaction types `TT09` (Fee) and `TT10` (Interest), and channels `C09` (Batch Processing) and `C10` (API).
- A Member whose only Posted Transactions in the 30-Day Window are institution-generated publishes `txn_count_30d = 0` — this is correct behavior, not a defect.
- A Member with no qualifying Transactions in the 30-Day Window publishes `0`, not null, for both 30-day measures.
- Window boundaries are inclusive of the As-Of Date, computed on calendar days, and keyed on **posting date** rather than authorization date.
- Amounts are typed decimal; currency-formatted source strings are parsed before aggregation.
- `[ASSUMPTION]` Channel Group `System` is institution-generated in all cases. `C10` (API) is the uncertain one — if the client exposes a member-facing API or open-banking integration, API traffic is member-initiated and this exclusion is wrong. See §8 Open Question 7.
- `[ASSUMPTION]` All amounts are USD and no currency conversion is required — every sample row carries `currency_code = 'USD'`. A non-USD row should fail the Daily Run rather than be silently summed.

#### FR-7: Derive recency fields

Each Member row carries when they last transacted and how long ago that was. Realizes UJ-2.

**Consequences (testable):**
- `last_txn_date` is the maximum Member-Initiated Transaction date for that Member on or before the As-Of Date; null only when the Member has never transacted. An interest posting does not refresh this field — which is the entire point of it.
- `days_since_last_txn` is the whole-day difference between `last_txn_date` and the As-Of Date; null when `last_txn_date` is null.
- Both fields are consistent with `txn_count_lifetime` — a Member with `txn_count_lifetime = 0` has null in both, and no Member with a non-null `last_txn_date` has `txn_count_lifetime = 0`.

#### FR-8: Carry channel and category rollups

Each Member row carries their dominant Channel Group and Transaction Category, plus a digital activity count. Realizes UJ-2.

**Consequences (testable):**
- `primary_channel_group` is the Channel Group accounting for the most Member-Initiated Transactions in the 30-Day Window; ties broken deterministically so the value is stable across re-runs.
- `primary_txn_category` is derived the same way from Transaction Category.
- `digital_txn_count_30d` counts Member-Initiated Transactions in the 30-Day Window whose Channel Group is `Digital`.
- A Member with no 30-Day activity publishes null for both primary fields and `0` for `digital_txn_count_30d`.

#### FR-9: Derive Activity Status

Each Member is classified by observed behavior, independently of their source-declared Relationship Status. Realizes UJ-2.

**Consequences (testable):**
- `activity_status` is `Active`, `Lapsing`, or `Inactive` for every Member — never null.
- Classification is a pure function of `days_since_last_txn`; a Member with a null `days_since_last_txn` is `Inactive`.
- `activity_status` is computed, never read from source, and does not overwrite `relationship_status` — both columns are published.
- The value `Dormant` does not appear in this column. See §3 Glossary.
- `[ASSUMPTION]` Thresholds are `Active` ≤ 30 days, `Lapsing` 31–90 days, `Inactive` > 90 days or never. The 90-day boundary is the common operational inactivity threshold in retail banking, which makes it defensible as a default — but there is no single industry standard, and credit union member-facing policies frequently use 12 months instead. Confirm against the client's own definition before this reaches a dashboard; see §8 Open Question 2.

**Feature-specific NFRs:**
- `activity_status` must not be used, cited, or interpreted as a determination of dormancy for unclaimed-property or escheatment purposes. Those determinations run on a multi-year, state-specific clock and are the responsibility of the system of record, not an analytical table.

**Notes:** `[NOTE FOR PM]` The disagreement between `relationship_status` and `activity_status` is arguably more interesting than either column alone — a Member the source calls Active who has not transacted in 120 days is exactly the retention target Renata is hunting in UJ-2. Worth a dashboard tile in its own right, but that is the analyst's call, not a table requirement.

---

### 4.4 Publication to Unity Catalog

**Description:** The product is published as a managed table in the client's Unity Catalog. Publication is not just a write — it includes the metadata that makes the table self-describing, because UJ-1 depends on Renata understanding the table from the catalog browser without asking anyone, and UJ-3 depends on her being able to verify freshness from the data itself.

**Functional Requirements:**

#### FR-10: Publish to Unity Catalog

`DP_Member_360` is written to Unity Catalog on each successful Daily Run. Realizes UJ-1.

**Consequences (testable):**
- The table is queryable via standard SQL with no joins required to answer "activity by segment."
- Publication is atomic — a reader querying during a Daily Run sees either the complete prior version or the complete new version, never a partial write.
- A failed Daily Run leaves the previous version intact and queryable.
- Schema is enforced on write; a type or column mismatch fails the run rather than silently coercing. An **additive** column is permitted and non-breaking (§11); a type change or removal is not.
- The table is marked as certified in the catalog, so it is visually distinguishable in the catalog browser from scratch and intermediate tables. This is what tells Renata she has found the right table in UJ-1 — without it, a governed product and someone's working copy look identical.
- Publication restores cleanly to a prior version if a bad run is published, without re-running the pipeline.
- `[ASSUMPTION]` The published name is `DP_Member_360` as given. Note this departs from the prevailing Unity Catalog convention of lowercase snake_case with the layer expressed in the catalog or schema rather than a table prefix — `prod.gold.member_360` would be idiomatic. Worth one minute of the client's time to confirm before the name is baked into a dashboard; renaming later is a breaking change.

#### FR-11: Publish freshness and lineage markers

Every row carries the information an analyst needs to judge whether to trust it. Realizes UJ-3.

**Consequences (testable):**
- `as_of_date` is present on every row and identical across all rows in a given Daily Run.
- `dp_load_ts` records when the Daily Run completed.
- Table-level and column-level comments are populated — at minimum stating the grain (one row per Member), the **Member-Initiated rule and what it excludes**, the meaning of the two windows, and that `activity_status` is derived while `relationship_status` is sourced.
- The Member-Initiated exclusion is stated in the table comment specifically because it makes activity counts lower than a naive count against the Transaction source. An analyst who reconciles the two without knowing the rule will conclude the pipeline is dropping rows.
- Both markers are queryable by the analyst without special permissions.

---

### 4.5 Data Quality and Observability

**Description:** A data product that is silently wrong is worse than one that is loudly broken, because the wrong number reaches a board pack. Quality checks run as part of the Daily Run and gate publication. The bar for v1 is a small set of checks that catch the failures that actually happen — not an exhaustive quality framework.

**Functional Requirements:**

#### FR-12: Gate publication on quality checks

Quality checks run before publication and a failure blocks the write.

Checks are organized against the six standard data quality dimensions, so the set is recognizable to a client data governance function rather than looking ad hoc.

**Consequences (testable):**
- **Uniqueness** — `member_id` is unique across the published table; a duplicate fails the run.
- **Completeness** — `member_id`, `member_segment`, `as_of_date`, and `activity_status` are non-null on every row; a null fails the run. Published row count reconciles to the distinct Member count in the Member Source Extract.
- **Validity** — `member_segment`, `activity_status`, `kyc_status`, `risk_rating`, and `primary_channel_group` contain only their documented permitted values; `home_state` is a recognized US state or DC; all count and amount measures are `>= 0`. An unrecognized value fails the run.
- **Consistency** — the recency/lifetime agreement stated in FR-7 holds for every row, and `txn_count_30d <= txn_count_lifetime` for every Member.
- **Timeliness** — `as_of_date` is the expected business date for the run. A stale As-Of Date fails rather than republishing yesterday's numbers under today's timestamp, which is the failure mode that silently breaks UJ-3.
- **Accuracy** — total 30-day transaction amount reconciles to an independent aggregate over the Transaction Source Extract, filtered by the same Member-Initiated rule, within a stated tolerance. `[ASSUMPTION]` Tolerance is zero for a full-recompute pipeline at this scale; a non-zero tolerance would only be warranted if the pipeline later becomes incremental.
- A check failure leaves the previously published table intact (per FR-10) and surfaces which check failed, on how many rows, and with what sample values.

#### FR-13: Report run outcome

Each Daily Run reports whether it succeeded, when, and over what volume.

**Consequences (testable):**
- Run status, As-Of Date, row count published, and quality check results are recorded and retrievable after the run.
- A failed or skipped Daily Run is visible to an operator without inspecting the table itself.
- `[ASSUMPTION]` Alerting is to an operational channel the client already runs; this PRD does not specify the mechanism. Deferred to architecture.

---

## 5. Non-Goals (Explicit)

- **Not real-time.** Daily batch is the contract. If a stakeholder needs intraday member activity, that is a different product with a different architecture — do not incrementally shorten the refresh interval toward streaming.
- **Not a system of record.** Nothing writes back to source microservices. The product is strictly read-downstream.
- **Not a carrier of direct identifiers.** Names, postal codes, and account numbers are excluded by design (FR-4). "Just add the member name so we can action the list" is the single most likely scope-creep request and it is explicitly out — it changes the governance classification of the entire table. Note this is a non-goal about *direct identifiers*, not a claim that the table is free of personal data; it is not (§10).
- **Not a dormancy or escheatment determination.** `activity_status` is an analytical convenience on a 90-day clock. Unclaimed-property dormancy runs on a multi-year, state-specific clock and belongs to the system of record. Do not wire this column into anything with a legal consequence.
- **Not a replacement for the Transaction fact.** Deep drill-down to individual transactions stays in the source layer. This product carries aggregates only.
- **Not a feature store.** No point-in-time correctness guarantee; measures are as-of-latest-run only. Do not train models on it.
- **Not multi-entity.** One credit union, one currency, one catalog.
- **Not a dashboard.** The product is the table and its contract. The dashboard is Renata's work product and is out of scope.

---

## 6. MVP Scope

### 6.1 In Scope

- Daily batch pipeline ingesting all eight Source Extracts.
- `DP_Member_360` published to Unity Catalog: one row per Member, the 10 existing profile attributes plus account rollups, windowed activity measures, channel/category rollups, recency fields, derived Activity Status, and freshness markers — 26 columns total.
- 30-Day, Prior 30-Day, and Lifetime windows. The prior window delivers period-over-period comparison without retaining history.
- Posted-only activity measurement.
- The five quality checks in FR-12, gating publication.
- Table and column comments sufficient for an analyst to self-serve.

### 6.2 Out of Scope for MVP

- **Trend over many periods (a time-series chart).** The Prior 30-Day Window (FR-6) delivers **one** comparison — current versus prior period — which covers the headline metric and the UJ-2 drop-off list. It does not deliver a line chart over twelve weeks, because the product retains no history. `[NOTE FOR PM]` If a multi-period trend chart turns out to be required, the agreed next step is a narrow segment-level daily history table — roughly four rows per day, an afternoon of work, and nothing built for v1 is wasted. See addendum §A3.
- **Additional time windows** (7-day, 90-day, quarter-to-date). Deferred because each is an additive column change and we do not yet know which Renata needs. Revisit after first dashboard use.
- **Product and Branch rollups.** The Product and Branch extracts are ingested but not surfaced as Member-level attributes in v1. Deferred as unproven — no stated question needs them. Low cost to add.
- **Segment-change tracking.** A Member moving from Student to Retail overwrites in place; no SCD history. Deferred to v2.
- **Automated alerting** on quality failures beyond the run report in FR-13.
- **Backfill** of historical As-Of Dates. v1 goes forward from first run.

---

## 7. Success Metrics

**Primary**

- **SM-1: Single-query sufficiency.** Renata produces the "activity by segment" view — **including the change against the prior period** — from one query against `DP_Member_360` with zero joins to other tables. Target: achieved on first attempt, without asking the build team what a column means. Validates FR-6, FR-8, FR-10, FR-11.
- **SM-2: Follow-up survivability.** The "which Premium members went quiet, and were they digitally enrolled" question (UJ-2) is answerable from the same table, also without joins. Target: achieved. Validates FR-7, FR-8, FR-9.

**Secondary**

- **SM-3: Freshness.** The published table carries an `as_of_date` of the prior business day by the agreed delivery time on at least 95% of business days. Validates FR-11, FR-2.
- **SM-4: Quality gate effectiveness.** Zero Daily Runs publish a table that subsequently fails one of the FR-12 checks. A blocked run is a success for this metric, not a failure. Validates FR-12.

**Counter-metrics (do not optimize)**

- **SM-C1: Column count.** **26 columns is the v1 budget**, raised once and deliberately from 24 to admit the Prior 30-Day measures. Growth is a warning sign, not progress — every "while you're in there, add..." makes the table harder to explain and slower to trust. The budget was raised by an explicit decision with a stated use case behind it; that is the only way it should ever move. Counterbalances SM-2: do not chase follow-up survivability by adding columns speculatively.
- **SM-C2: Freshness latency.** Do not optimize the pipeline toward intraday. Daily is the contract (§5) and a faster-than-daily pipeline would be a signal we built the wrong architecture. Counterbalances SM-3.

---

## 8. Open Questions

1. **`member_id` format contract.** The sample raw extract uses `M0001`; the sample product file uses `M000001` and carries 100 members against the raw extract's 10. The sample product was not generated from the sample sources. Which format is canonical, and is there a transformation rule, or is this purely a sample-data artifact? **Blocks FR-3.**
2. **Activity Status thresholds.** Are 30 / 90 days the right cut points for Active / Lapsing / Inactive? Research confirms there is **no single industry standard** — 90 days is a common operational inactivity threshold, but credit union member-facing policies frequently use 12 months, and the client may have its own definition already in use in other reporting. Publishing a column that disagrees with the institution's own published definition is worse than publishing no column. **Blocks FR-9.**
3. ~~**Trend capability.**~~ **RESOLVED 2026-10-01.** The gap was real — the headline metric reads as a trend and the wide table retains no history. Resolved by adding Prior 30-Day Window measures to the existing row (FR-6) rather than by retaining history: it delivers the current-versus-prior comparison the headline needs, with no new table, no grain change, and no snapshot double-count risk. Accepted limitation: one comparison, not a time series. Options considered and the reasoning are preserved in addendum §A3. *(Retained here rather than deleted so the decision trail survives.)*
4. **Delivery time.** SM-3 references "the agreed delivery time." What is it? Renata's UJ-3 happens at 8:15am, which implies the run must complete before then.
5. **Unity Catalog placement and grants.** Which catalog and schema does this land in, and who holds `SELECT`? Assumed broad analyst read given the de-identified design, but unconfirmed.
6. **Retention.** How long is a published version retained, and does the client have a stated retention policy this must conform to?
7. **Is the `API` channel member-initiated?** FR-6 excludes Channel Group `System`, which covers both `C09` Batch Processing and `C10` API. Batch is clearly institution-generated. API is not obvious — if the client exposes a member-facing API or participates in open banking, those are member actions and excluding them understates digital engagement for exactly the members most likely to be digitally engaged. **Blocks FR-6.**
8. **Does the client already publish a member activity metric?** If any existing report defines "active member," this product must either match it or explain why it differs. Two competing definitions of activity in one institution is a worse outcome than the current state of having none.

---

## 9. Assumptions Index

Every `[ASSUMPTION]` in this document, surfaced for explicit confirmation:

**Blocking — resolve before build:**

- **§4.2 / FR-3** — Canonical `member_id` format is the zero-padded `M000001` form, and the raw/product mismatch is a sample-data artifact rather than a real transformation rule. *(Open Question 1.)*
- **§4.3 / FR-6** — Channel Group `System` is institution-generated in all cases, including `C10` API. Wrong if the client runs a member-facing API. *(Open Question 7.)*
- **§4.3 / FR-9** — Activity Status thresholds of 30 / 90 days. Research confirms 90 days is a common operational threshold but **no single industry standard exists**, and credit unions often use 12 months. Client definition takes precedence if one exists. *(Open Questions 2 and 8.)*

**Non-blocking — confirm when convenient:**

- **§4.1 / FR-2** — Full recompute of the Lifetime Window on every run makes late-arriving data self-correcting, removing the need for an explicit lookback window. Holds only while full recompute remains practical at the client's data volume.
- **§4.3 / FR-6** — All transactions are USD; no currency conversion is required, and a non-USD row should fail the run rather than be silently summed.
- **§4.4 / FR-10** — The published name `DP_Member_360` is taken as given, despite departing from prevailing Unity Catalog naming convention. Cheap to change now, breaking to change later.
- **§4.5 / FR-12** — Accuracy reconciliation tolerance is zero, appropriate for a full-recompute pipeline at this scale.
- **§4.5 / FR-13** — Run alerting uses an operational channel the client already operates; mechanism deferred to architecture.
- **§10** — GLBA applies, implemented via NCUA Regulation P and Part 748. Verified as the correct regime for a US credit union in general; **not** verified against this client's own compliance posture.
- **§10** — The HIPAA Safe Harbor pattern is used as a design yardstick only and confers no legal status. If age bands are extended upward, 90+ collapses into one band.
- **Document-wide** — The client platform is Databricks, inferred from "Unity Catalog." Delta Lake is therefore the storage format. Named here because FR-10's atomicity, versioning, and schema-enforcement requirements assume it.
- **Document-wide** — The eight CSV extracts in `data/raw/` are faithful stand-ins for microservice feeds in both shape and semantics, and the real feeds will arrive on a comparable daily cadence.

---

## 10. Data Governance

- **Classification: pseudonymized, not anonymized.** This distinction is load-bearing and the document uses the narrower word deliberately. The product carries no direct identifiers (FR-4), but `member_id` remains a live key back to a fully identified Member record, and combining `age_band` + `home_state` + `member_since_date` + `total_current_balance` carries real re-identification risk in a small membership. Calling the table "anonymized" would invite access decisions it cannot support. Treat as internal-confidential NPI.
- **Identifier exclusion is a control, not a preference.** Any future request to add a name, postal code, or account number re-classifies the table and invalidates the broad-grant access model in Open Question 5. Such a request goes through governance review, not a schema change ticket.
- **Regulatory.** `[ASSUMPTION]` As a US credit union, GLBA is the governing privacy regime, implemented through **NCUA Regulation P** (privacy of consumer financial information) with the safeguards program under **NCUA Part 748 / Appendix A**. Account balances and transaction history are explicitly non-public personal information under that regime. Confirm with the client's compliance function before the table is granted beyond the build team.
- **No safe harbor exists.** GLBA provides no de-identification safe harbor comparable to HIPAA's, so there is no bright line this table can cross to become unregulated. The column design here deliberately mirrors the **HIPAA Safe Harbor** pattern as the recognizable yardstick — names and postal codes dropped, geography no finer than state, ages banded — because that is the standard a reviewer will recognize, not because it confers any legal status. `[ASSUMPTION]` If age bands are ever extended upward, ages 90+ should collapse into a single band, per the same convention.
- **Access controls.** Least-privilege grants to the analyst role; column masks or row filters available at the platform level should a future column warrant them. Classification and ownership expressed as catalog tags rather than tribal knowledge.
- **Lineage.** `as_of_date` and `dp_load_ts` (FR-11) provide row-level provenance for when; source extracts provide from-where. Full column-level lineage is deferred to the platform's native capability rather than being hand-maintained.
- **Retention.** Unresolved — Open Question 6.

---

## 11. Cross-Cutting NFRs

- **Freshness.** `as_of_date` reflects the prior business day on at least 95% of business days (SM-3). A missed run is visible (FR-13), never silent.
- **Idempotency.** Any Daily Run is safe to re-run for the same As-Of Date with identical results (FR-2). This is a hard requirement, not best-effort — operators will re-run.
- **Query performance.** A full-table `GROUP BY member_segment` returns interactively (single-digit seconds) at expected membership scale. The wide-table grain exists specifically to make this true without tuning.
- **Schema stability.** Additive column changes are non-breaking and may ship freely. Renaming or removing a published column, or changing a column's type or semantics, is breaking and requires notifying the analyst before the change ships — Renata's dashboard binds to these names.
- **Failure isolation.** A failure anywhere in the Daily Run leaves the prior published version intact and queryable (FR-10). Degraded freshness is always preferable to incorrect data.
- **Determinism.** Given identical source extracts and As-Of Date, output is identical — including tie-breaks in derived fields (FR-8).

---

## 12. Integration and Dependencies

**Upstream** — Eight Source Extracts: `Member`, `Account`, `Transaction` (the fact), and the `Product`, `Branch`, `Channel`, `Transaction_Type`, `Date` dimensions. Sample files in `{project-root}/data/raw/`. The pipeline is a consumer of these; it does not control their schedule, schema, or quality, which is precisely why FR-1 and FR-12 fail loudly rather than coping.

**Downstream** — One known consumer: the analyst's dashboard, reading `DP_Member_360` from Unity Catalog. Any additional consumer that appears post-launch inherits the schema-stability contract in §11 and should be recorded here.

**Platform** — The client's existing Unity Catalog. The product does not introduce new infrastructure; it publishes into infrastructure the client already operates.
