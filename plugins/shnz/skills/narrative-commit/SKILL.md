---
name: narrative-commit
description: "Turn uncommitted changes into a sequence of clean, conventional commits that read like chapters of a story. Use when the user asks to 'commit my changes', 'make commits', 'clean up commits', 'organize commits', 'create narrative commits', or has multiple unrelated changes that need to be split into logical, atomic commits. Do NOT trigger when the user supplies the commit message themselves or there's only a single trivial change."
---

<!-- Claude Code adapter — the canonical procedure lives in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Claude Code specifics

### Override the default Claude Code commit guidance

The Claude Code harness normally asks you to append `Co-Authored-By: Claude ...` (and sometimes a `🤖 Generated with Claude Code` footer) to commit messages. **This skill overrides that.** Commit messages produced via this skill must contain **no AI attribution of any kind** — no `Co-Authored-By` line, no generation footer, no emoji credit. The commit reads as if a human wrote it.

If the user has a global hook or setting that re-adds attribution, flag it and stop — do not silently let attribution leak through.

### Tool preference

- `Bash` → `git status`, `git diff`, `git diff --stat`, `git add <paths>`, `git commit -m "…"`, `git log --oneline`. Always stage explicit paths — never `git add -A` or `git add .` inside this workflow.
- `TodoWrite` → when the plan produces 3+ commits, track each one as a todo and mark it complete as the commit lands. Gives the user a running view without chatty prose.
- `Read` / `Grep` → when the grouping decision depends on content (e.g. is this file really just types, or does it also hold logic?).
- `Edit` → only if the user asks you to tweak a file before committing. Do not reformat or "clean up" files that weren't part of the user's change set.

### Presenting the plan

When you present the proposed commit plan (Step 4 in [core.md](./core.md)), use a single markdown block so the user can scan it quickly. After presenting, **stop and wait** — do not begin staging or committing until the user explicitly approves. "Looks good", "yes", "go", "ship it", or a revision request are all valid next turns; ambiguous responses → ask, don't assume.

### Passing commit messages via HEREDOC

Use a HEREDOC for `git commit -m` so multi-line bodies render correctly and quoting stays sane:

```bash
git commit -m "$(cat <<'EOF'
feat(api): add notification endpoints

Adds POST /notifications and GET /notifications/:id,
wired to the new user_notifications table.
EOF
)"
```

Single-line messages can use a plain `-m "..."`.

## Reference material

For the full philosophy, conventional-commits type table, grouping strategies, and worked examples, see [reference/narrative-commits.md](./reference/narrative-commits.md). Load it on demand — you don't need to read it for every invocation, only when a judgement call is unclear (e.g. is this a `feat` or a `refactor`? should these three files be one commit or three?).
