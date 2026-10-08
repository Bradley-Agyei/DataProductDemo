# Data products

Four data products, each built by a tested Python pipeline on the shared contract-driven framework `dp_framework`.

| Product | What it is | Start here |
|---|---|---|
| `DP_Member_360/` | One governed row per member, from the 8 extracts in `data/raw/` | `PRD_Member_360.md`, `04_code/README.md` |
| `DP_Fraud_Case/` | One governed row per fraud case, with lifecycle checks, SLA and member/account links | `PRD_Fraud_Case.md`, `04_code/README.md` |
| `DP_Payment_Transaction/` | One governed row per payment transaction (in progress: FR-01 raw ingestion, SCRUM-44) | `PRD_Payment_Transaction.md`, `04_code/README.md` |
| `DP_Account_Daily_Balance/` | One governed row per account per day (in progress: FR-07 publish, SCRUM-43) | `PRD_Account_Daily_Balance.md`, `04_code/README.md` |

Each product folder holds:
- the PRD (`.md` + `.docx`) and data dictionary (`.xlsx`), with a data type for every column
- `stories.md`: Jira stories, with each acceptance criterion linked to its test
- `Unit_Test_Cases_*.md/.xlsx`: every test case, generated from a real pytest run
- `04_code/`: contracts, pipeline, generated DDL and tests

Shared pieces:
- `../tools/`: builds and validates the account ID mapping table and generates the unit test case documents
- `../data/reference/account_id_map.csv`: maps each system's account ID format to canonical `A` + 7 digits
- `../openspec/specs/`: behaviour specs (`data-products/fraud-case`, `identity/account-id-conformance`)

Rules followed (see `CLAUDE.md`):
- Existing `data/raw/` files are unchanged; `data/raw/DP_Fraud_Case.csv` is a new extract.
- No PII (names, postal code) appears in any product, test, or document. Tests that need a member row read it from the file at runtime.

## Run everything
```bash
pip install pandas pytest python-docx openpyxl
cd output/DP_Member_360/04_code && pytest -q && python -m src.member_360.run --as-of 2026-10-04
cd ../../DP_Fraud_Case/04_code && pytest -q && python -m src.fraud_case.run --as-of 2026-10-04
cd ../../.. && python -m pytest -q tools/tests
python -m tools.build_unit_test_cases member_360   # or fraud_case
```
Run Member 360 before Fraud Case: Fraud Case reads `member_360.csv` from Member 360's output.
