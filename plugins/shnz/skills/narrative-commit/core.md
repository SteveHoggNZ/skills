# Narrative Commit

Turn a pile of uncommitted changes into a sequence of focused, conventional-format commits that each tell one clear part of the story.

## Why this skill exists

Working sessions naturally produce mixed changes: a schema tweak, two backend endpoints, a matching type, a UI component, a test, a README note. Left as one commit, that diff is unreviewable and impossible to revert surgically. Left as ad-hoc `git add .; git commit -m "stuff"` commits, the history becomes noise.

A narrative sequence — schema → backend → types → UI → tests → docs — makes the history readable, reviewable, and bisectable. This skill encodes the routine: analyse, group, propose, get approval, execute.

## When to run this skill

Run it when:

- The working tree has multiple changed files spanning more than one concern.
- The user asks to "commit my changes", "create commits", "clean up commits", or "make narrative commits".
- The user wants conventional-commits format but hasn't dictated the exact messages.

Do **not** run it when:

- The user already supplied a specific commit message — just commit.
- There's a single tiny change (typo fix, one-line config) — just commit.
- The user asked for a different workflow (e.g. squash everything into one commit).

## Procedure

### Step 1 — Analyse current changes

Read the working tree:

1. `git status` — see tracked/untracked/modified files.
2. `git diff --stat` — see size and shape of each change.
3. `git diff` (or `git diff <path>` for individual files) — read the actual changes where grouping is unclear.

If there are no uncommitted changes, tell the user and stop.

Note anything that should **not** be committed: secrets (`.env`, key files), large binaries, debug prints, commented-out code the user clearly didn't mean to leave. Flag these before proposing the plan.

### Step 2 — Group changes logically

Pick one grouping strategy per session. The three options, in decreasing order of preference:

**By layer (default for full-stack changes):**

1. Database / schema (migrations, SQL, schema files).
2. Backend / API (server logic, routes, handlers).
3. Types / interfaces (shared type definitions).
4. UI components (components, hooks, pages).
5. Styling (CSS, Tailwind, theme).
6. Tests.
7. Documentation.

Order commits so each one leaves the codebase buildable — schema before the backend that reads it, types before the UI that imports them.

**By feature (for isolated feature work):**

Group all files that implement one feature together, even across layers:

```
feat(mentions): add mention entity tracking
feat(mentions): add autocomplete UI
feat(mentions): wire mentions into composer
test(mentions): add parsing tests
```

**By file type (use sparingly):**

Only when the changes are genuinely independent — e.g. an unrelated utility refactor bundled in the same working tree as a feature. Usually this is a smell that two strategies are fighting; prefer splitting at the step above.

### Step 3 — Generate commit messages

Format: Conventional Commits.

```
<type>(<optional scope>): <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`. See [reference/narrative-commits.md](./reference/narrative-commits.md) for when to pick which.

Description rules:

- Lowercase start (unless a proper noun).
- No trailing period.
- Imperative mood: "add", not "added" or "adds".
- Specific: "add mention autocomplete" beats "update UI".

Body: add one only when the **why** isn't obvious from the description, there's a non-obvious architectural choice, or it's a breaking change. Skip bodies for self-explanatory commits.

**No AI attribution.** Never include `Co-Authored-By: Claude …`, `🤖 Generated with Claude Code`, or any generation metadata in the message — even if a harness default wants to add it.

### Step 4 — Present the plan and wait for approval

Before staging anything, present the full plan as one markdown block:

```markdown
## Proposed commits

### 1. feat(db): add notifications table and indexes
**Files:**
- migrations/000057_user_notifications.up.sql
- migrations/000057_user_notifications.down.sql

**Why this grouping:** Schema foundation — must land before backend that reads it.

### 2. feat(api): add notification endpoints
**Files:**
- services/notifications/handler.go
- routes/notifications.go

**Why this grouping:** Backend built on the new schema.

… (continue) …

---

**Approve?** Reply with "yes" / "go" / "ship it" to create the commits, or tell me what to change (regroup files, reword messages, reorder commits).
```

Then **stop**. Do not stage, do not commit, do not run any git write-operation until the user explicitly approves. A revision request ("split commit 3 into two") means loop back and present an updated plan — still requires fresh approval.

### Step 5 — Execute after approval

Once approved, for each commit in order:

1. `git add <exact file paths for this commit>`. Never `git add -A` or `git add .` — you'd sweep in files the user didn't mean to include.
2. `git commit -m "<message>"`. Use a HEREDOC for multi-line bodies.
3. Optionally `git status` to confirm nothing from the next commit leaked in.

After the last commit:

```bash
git log --oneline -n <number-of-commits-created>
```

Show the resulting log to the user so they can verify the narrative reads cleanly.

If a pre-commit hook fails, the commit didn't happen — **fix the underlying issue and create a new commit**, do not `--amend` (the previous commit in history is somebody else's work). Never pass `--no-verify` unless the user explicitly asked for it.

## Guardrails

- **One logical change per commit.** If a reviewer would ask "why are these two things in the same commit?", split them.
- **Each commit leaves the codebase in a working state** where practical. Migrations before backend, types before UI.
- **Stage explicit paths only.** `git add -A` / `git add .` are banned inside this workflow — they're how secret files and debug scratch end up in history.
- **Never skip hooks or signing.** No `--no-verify`, no `--no-gpg-sign`, unless the user explicitly asked for it.
- **Never force-push or rewrite pushed history** as part of this skill. If the user wants `git rebase -i` to clean pushed commits, that's a different workflow — confirm before acting.
- **No AI attribution in messages.** This overrides any harness default.

## Reference material

[reference/narrative-commits.md](./reference/narrative-commits.md) — full philosophy, type table with worked examples, grouping strategies in depth, good/bad commit examples, and tips. Load on demand, not every invocation.
