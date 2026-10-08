# Tasks

## 1. Skill

- [x] 1.1 Add `.claude/skills/llm-wiki/SKILL.md` with its paths adapted (`wiki/raw/`, `wiki/output/`) and a "This repo" note. Verify: no reference to a top-level `raw/` or `output/` remains outside that note.
- [x] 1.2 Change `.gitignore` to `.claude/*` plus `!.claude/skills/`. Verify: `git check-ignore` ignores `.claude/settings.local.json` and not the skill.

## 2. Wiki scaffold and docs

- [x] 2.1 Scaffold `wiki/`: `index.md` and `log.md` (with a setup entry), and the `raw/`, `output/`, `sources/`, `concepts/`, `entities/` and `syntheses/` folders.
- [x] 2.2 Update the CLAUDE.md structure section and add `docs/kt/llm-wiki/README.md`.
