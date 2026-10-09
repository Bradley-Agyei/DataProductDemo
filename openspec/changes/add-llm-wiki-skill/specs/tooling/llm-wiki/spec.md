# Spec Delta

## Purpose

Defines the project LLM Wiki and keeps it apart from the data pipeline.

## ADDED Requirements

### Requirement: Wiki stays out of the data pipeline
The llm-wiki skill SHALL read sources only from `wiki/raw/` and SHALL write only under `wiki/`. It SHALL NOT write to `data/raw/` or `output/`.

#### Scenario: Ingest a source
- **WHEN** a source is ingested
- **THEN** it is saved in `wiki/raw/`, and the pages, `index.md` and `log.md` under `wiki/` are updated

#### Scenario: Deliverable from the wiki
- **WHEN** a report is produced from the wiki
- **THEN** it is written to `wiki/output/`, not `output/`

### Requirement: Wiki sources are read-only
The skill SHALL NOT edit or delete files in `wiki/raw/`, and SHALL NOT delete wiki pages without asking.

#### Scenario: Lint finds a problem in a source
- **WHEN** a lint pass finds a stale or conflicting claim
- **THEN** it reports the problem, and fixes wiki pages only with the user's OK, never the source file

### Requirement: No PII in the wiki
Wiki pages SHALL NOT contain PII (names, addresses, postal codes), in line with CLAUDE.md.

#### Scenario: Source mentions member data
- **WHEN** an ingested source refers to member records
- **THEN** the wiki page describes columns and rules, never member values

### Requirement: Shared skills are tracked
`.claude/skills/` SHALL be tracked in git, while other `.claude/` files (local settings) stay ignored.

#### Scenario: Local settings
- **WHEN** `.claude/settings.local.json` exists
- **THEN** git ignores it, and `.claude/skills/llm-wiki/SKILL.md` is tracked
