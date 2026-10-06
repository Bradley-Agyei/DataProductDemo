# Left-shift gates: knowledge transfer

## What this is

The repo's rules used to live only in `CLAUDE.md`: `data/raw/` is read-only, PII never leaves it, and every requirement is specified and tested. Now each rule is a check. It runs on your machine before the commit (lefthook), and again on GitHub before the merge, with the same command in both places.

| Required check | Question | Local | GitHub |
|---|---|---|---|
| `ci` | Does it still work, and is the data safe? | pre-commit | Linux + Windows |
| `spec-gate` | Did you build what the spec promised? | pre-commit L0-L2, pre-push L3-L5 | L0-L5 |
| `attest` | Did the local run, including the Claude review, happen on this exact tree? | pre-commit (writes it) | verifies it, never calls a model |
| `kt-docs` | Did you leave the next person a map? | pre-push | every PR |

## Setup, once

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install "./tools/specgate[dev]"
```

On macOS or Linux the interpreter is `.venv/bin/python`. Then install the hooks; this needs lefthook (`winget install evilmartians.lefthook`, or `brew install lefthook`):

```bash
lefthook install
```

You also need Node 22 (for `npx`) and Claude Code logged in (`claude auth login`). The attestation calls `claude -p`.

## What happens on commit

With the venv active, `git commit` runs `python tools/leftshift/attest.py make`, which:

1. runs the gates in order and stops at the first red one: `raw`, `pii`, `openspec`, `scenarios`, `specgate` (L0-L2; also regenerates and stages each `trace.json`), `unittest`;
2. if all pass, sends the staged files, minus `data/`, CSVs, `.attestations/` and the vendored `tools/specgate/`, to a headless Claude review with no tools;
3. re-checks every finding's file, line and quote against the code. A finding that points at nothing is ignored;
4. fails if any HIGH finding checks out. Otherwise it writes `.attestations/attestation.a2a.json` (an A2A v1.0 Task) and stages it into the same commit.

## What CI checks

`attest verify` fails when the attestation is:

- missing (the hooks were skipped);
- stale (code changed after the review);
- not `TASK_STATE_COMPLETED` with verdict `pass`;
- missing a gate, or recording a red one;
- holding a HIGH finding that still matches the code.

It never calls a model.

## Gotchas

- **Rebasing makes the attestation stale.** The digest covers the whole tree, so commit again (or `git commit --amend`) to re-attest.
- **`attest` proves the run happened; it does not prove honesty.** The digest is a public function of the tree, so a determined person could hand-write the JSON. That is why `.attestations/` is in `CODEOWNERS`.
- **`openspec validate --strict` accepts a requirement with no scenario.** We checked against a real change, so `checks.py scenarios` enforces it instead.
- **specgate lives here.** `tools/specgate/` is owned by this repo (see `VENDORED.md` for where it came from and what changed). Its `.specgate-skip` keeps its own `# implements:` markers out of this repo's trace, and it never walks into a directory with its own `.git`, so a worktree kept inside the repo does not double the trace.
- **A change with no `prd.md` is not traced.** spec-gate prints `NOT TRACED: <change> has no prd.md`. Its OpenSpec structure and scenarios are checked; AC-to-test traceability is not.
- **The review covers the whole branch.** `attest make` reviews every file changed since the branch left `upstream/main` (or `origin/main`; set `LEFTSHIFT_BASE` to override), not just the commit being made. Binary files (xlsx, docx) are named but never sent.
- **Tests that create git repos must strip `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE`.** Inside a hook those point at this repo.

## Making the checks required

Until a ruleset is set, a red check is advice. A repository admin applies [`ruleset.json`](ruleset.json) once:

```bash
gh api -X POST repos/Bradley-Agyei/DataProductDemo/rulesets --input docs/kt/left-shift-gates/ruleset.json
```

It requires all five checks on an up-to-date branch, a PR with one approval from a code owner who is not the last pusher, and it blocks force-pushes and deleting `main`. Admins can bypass, but only through a PR, and that shows in the audit log.

- **"Up to date" protects the attestation.** When the head already contains `main`, a merge or squash produces exactly the attested tree.
- **A solo maintainer cannot approve their own push.** Someone else must review.

`actor_id` 5 is the admin repository role. GitHub's REST docs do not list role ids; the value comes from the Terraform provider docs.

## After a merge

A clean `git merge` does not run the pre-commit hook, so the merge commit carries no fresh attestation. The next commit re-attests, or run `git commit --amend --no-edit` to attest the merge itself.

## Run CI locally

`act` runs the workflows in Docker; with colima, run it inside WSL. The kt-docs check reads the changed files from the event payload:

```bash
act pull_request -W .github/workflows/kt-docs.yml -e .github/act-events/pr-docs-kt.json -P ubuntu-24.04=catthehacker/ubuntu:act-latest
```

```bash
act pull_request -W .github/workflows/kt-docs.yml -e .github/act-events/pr-code-only.json -P ubuntu-24.04=catthehacker/ubuntu:act-latest
```

The first should pass and the second should fail.
