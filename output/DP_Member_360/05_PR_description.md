## SCRUM-17: Member 360 data product – PRD, contracts, build framework and tests

**Jira:** [SCRUM-17](https://monishapm.atlassian.net/browse/SCRUM-17) (Feature epic) · stories [SCRUM-18](https://monishapm.atlassian.net/browse/SCRUM-18)–[SCRUM-24](https://monishapm.atlassian.net/browse/SCRUM-24)

### Summary
- Builds `member_360`, one governed, typed row per member, from 8 banking source CSVs.
- Column types are defined once, in the contracts (60 source columns, 12 product columns). Parsing, DDL, DQ, CSV export and the data contract are all generated from them.
- `src/dp_framework/` is generic and reusable for the next data product. `src/member_360/` holds only the product-specific rules.

### What changed
| Path | What |
|---|---|
| `data/raw/*.csv` | 8 source files (sample data) |
| `data/product/DP_Member_360.csv` | Target sample: defines the product's columns and their order |
| `output/DP_Member_360/PRD_Member_360.{md,docx}` | PRD with full data dictionary, S2T mapping, DQ rules, open questions |
| `output/DP_Member_360/Data_Dictionary_Member_360.xlsx` | Source, target and mapping sheets |
| `output/DP_Member_360/stories.md` | Each story's acceptance criteria → test |
| `output/DP_Member_360/04_code/contracts/` | Source and product contracts |
| `output/DP_Member_360/04_code/src/dp_framework/` | types, ingest, standardize, dq engine, load (SQLite), publish |
| `output/DP_Member_360/04_code/src/member_360/` | config, transform, dq_rules, exceptions, run (CLI) |
| `output/DP_Member_360/04_code/sql/ddl/` | DDL generated from the contracts |
| `output/DP_Member_360/04_code/tests/` | 98 pytest tests |
| `workflows/prd-to-data-product.md` | Reusable recipe: source data → PRD → Jira → code |

### Story → test traceability
| Story | Jira | Status | Tests |
|---|---|---|---|
| FR-01 Ingest sources | SCRUM-18 | Done | `test_ingest.py` |
| FR-02 Standardize data types | SCRUM-19 | Done | `test_types.py`, `test_standardize.py` |
| FR-03 Conform member ID | SCRUM-20 | Done | `test_member_id.py` |
| FR-04 Build core columns | SCRUM-21 | Done (Restricted rule is a switch until Q5 is decided) | `test_build_core.py` |
| FR-05 New attribute feeds | SCRUM-22 | Partly done: typed, published as NULL; blocked on feeds | `test_pending_attributes.py` |
| FR-06 DQ and exceptions | SCRUM-23 | Done | `test_dq.py` |
| FR-07 Publish and govern | SCRUM-24 | Done locally; catalog and access roles are platform tasks | `test_publish.py` |

### How to test
```bash
cd output/DP_Member_360/04_code
pip install pandas pytest
pytest -q
python -m src.member_360.run --as-of 2026-10-04
```

### Test results
- `pytest -q` → **98 passed**
- Pipeline run → **SUCCESS**: 10 rows in `member_360`, 0 rejects, every DQ rule (DQ-01 to DQ-10) Pass, 22 exceptions reported (2 negative balances on A00003; 20 transactions by Dormant members on Restricted accounts)

### Open questions (see PRD section 11)
- Q1/Q2: Target sample IDs (`M000001`…`M000100`) don't match the source IDs (`M0001`…`M0010`). The sample is used only for its columns and order.
- Q3/Q4: No source yet for age_band, kyc_status, risk_rating, last_profile_update_ts. The digital_enrolled_flag definition also needs a decision.
- Q5: Approve the rule "a member with any Restricted account is Restricted".

### Checklist
- [x] Tests pass
- [x] DDL in sync with contracts (enforced by a test)
- [x] Docs updated (README, PRD, stories, workflow)
- [x] No secrets, no PII in the product (names and postal code excluded)
- [x] Generated files (`*.db`, `out/`) are git-ignored
