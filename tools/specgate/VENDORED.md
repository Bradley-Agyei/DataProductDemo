# specgate (owned by this repo)

The spec gate this repo runs: PRD schema, static checks, AC traceability,
tests, per-AC coverage and mutation (L0-L5). It started as a copy of
`plugins/specgate` from harness-engineering-demo (commit `b84df18`) and is now
maintained here; there is no upstream to sync with.

Changes made here since the copy:

- Directories holding their own `.git` (worktrees, submodules, clones) are
  never walked or copied into the L5 sandbox. A worktree kept in a gitignored
  folder doubled every AC's markers.

Rules:

- `.specgate-skip` keeps specgate's own `# implements:` markers out of this
  repo's AC trace. Do not delete it.
- specgate has no tests of its own in this repo; a change here is checked by
  running the gate on `openspec/changes/left-shift-gates` (L0-L5) before merge.
