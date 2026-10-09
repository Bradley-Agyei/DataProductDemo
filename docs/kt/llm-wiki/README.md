# LLM Wiki: knowledge transfer

## What this is

A project wiki that an agent maintains, after Andrej Karpathy's LLM Wiki idea. You drop a source (PRD, transcript, article, notes) into `wiki/raw/` and say "ingest". The agent writes a summary page, updates the concept and entity pages the source touches, cross-links them and logs the change. Ask "what does the wiki say about…" to query it, and "lint the wiki" for a health check.

| Piece | What it is |
|---|---|
| `.claude/skills/llm-wiki/SKILL.md` | The skill: layout, page conventions, and the ingest, query and lint steps |
| `wiki/raw/` | Wiki sources. Read-only once added. |
| `wiki/sources/`, `concepts/`, `entities/`, `syntheses/` | Pages the agent writes |
| `wiki/index.md` | Catalog of every page |
| `wiki/log.md` | Append-only history of ingests, queries and lints |
| `wiki/output/` | Reports and drafts made from the wiki |

## Why the paths differ from the original skill

The original skill uses a top-level `raw/` for sources and `output/` for deliverables. Here, `data/raw/` is the pipeline's read-only extracts, and `output/` holds the data products. So the wiki keeps both inside `wiki/`, and never writes to `data/raw/` or `output/`.

## Things to know

- **No PII in the wiki.** CLAUDE.md still applies: describe columns and rules, never member values.
- **Only `.claude/skills/` is tracked.** `.gitignore` ignores the rest of `.claude/`, including local settings.
- **It starts empty.** Good first sources are the two PRDs (`output/DP_Payment_Transaction/PRD_Payment_Transaction.md` and `output/DP_Account_Daily_Balance/PRD_Account_Daily_Balance.md`). Copy them into `wiki/raw/` before ingesting.
