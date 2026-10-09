# Proposal

## Why

Product knowledge (PRDs, decisions, open questions, Jira context) is spread across documents and is re-researched every time it's needed. The `llm-wiki` skill (after Andrej Karpathy's LLM Wiki idea) keeps a persistent, interlinked markdown wiki that grows with each source.

## What Changes

- **New skill:** `.claude/skills/llm-wiki/SKILL.md`, with three operations: ingest, query and lint.
- **Paths adapted to this repo:**
  - Wiki sources go in `wiki/raw/`, not a top-level `raw/`, so they can't be confused with the read-only `data/raw/` extracts.
  - Deliverables go to `wiki/output/`, not `output/`, which holds the data products.
  - The skill states that the CLAUDE.md PII rule applies to wiki pages.
- **`.gitignore`:** `.claude/` becomes `.claude/*` plus `!.claude/skills/`, so shared skills are tracked and local settings stay ignored.
- **`wiki/` scaffold:** `index.md` and `log.md`, plus empty `raw/`, `output/`, `sources/`, `concepts/`, `entities/` and `syntheses/` folders.
- **Docs:** CLAUDE.md's structure section and the KT doc `docs/kt/llm-wiki/README.md`.

No code or data-product behaviour changes.

## Capabilities

### New Capabilities
- `tooling/llm-wiki`: a maintained project wiki, kept separate from the data pipeline.

## Impact

- New: `.claude/skills/llm-wiki/`, `wiki/` and `docs/kt/llm-wiki/README.md`.
- Changed: `.gitignore` and `CLAUDE.md`.
