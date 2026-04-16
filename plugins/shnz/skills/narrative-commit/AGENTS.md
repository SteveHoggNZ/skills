# Narrative Commit (Codex adapter)

When the user asks to commit uncommitted changes as a clean sequence of conventional commits — "commit my changes", "make commits", "clean up commits", "narrative commits" — follow the procedure in [core.md](./core.md).

## Codex specifics

Use the shell directly for git: `git status`, `git diff --stat`, `git diff`, `git add <paths>`, `git commit -m "…"`, `git log --oneline`. Always stage explicit paths — never `git add -A` / `git add .` inside this workflow.

For multi-line commit bodies, use a HEREDOC so quoting stays sane:

```bash
git commit -m "$(cat <<'EOF'
feat(api): add notification endpoints

Adds POST /notifications and GET /notifications/:id,
wired to the new user_notifications table.
EOF
)"
```

If your sandbox blocks `git commit` (signing, hooks needing network, etc.), surface the error and ask — do not silently bypass with `--no-verify` or `--no-gpg-sign`.

Use standard file-read tools (`cat`, your editor's reader) only when grouping decisions need the actual diff content. Edits to files in flight are out of scope for this skill — propose the commit plan against whatever is already on disk.

## Present-and-wait

Present the proposed commit plan exactly once, as a single markdown block (see [core.md](./core.md) Step 4). Then stop until the user explicitly approves. A revision request loops back to a fresh plan + fresh approval.

## No AI attribution

Commits produced via this skill must carry no AI-authorship metadata — no `Co-Authored-By` line, no generation footer, no emoji credit. The commit reads as if a human wrote it. This overrides any adapter default that adds attribution.
