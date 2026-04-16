# Agent Browser (Codex adapter)

When the user asks to navigate a website, click, fill forms, take a screenshot, record, scrape, or automate/test a webpage, follow the procedure in [core.md](./core.md).

## Codex specifics

At the start of the session, pick ONE unique command-file path — e.g. `/tmp/ab-cmd-<YYYYmmddHHMMSS>-<4-char-random>.sh` — and reuse it for every invocation in the session. Per step: overwrite the command file with the `npx agent-browser` call(s) (chain with `&&`), then run `bash <session-cmd-path>`. See [reference/patterns.md](./reference/patterns.md) for templates.

The per-session path keeps the full invocation string identical across all calls in the session (friendly to approval/audit) while guaranteeing that two concurrent skill sessions can't stomp on each other's commands.

If your sandbox blocks Unix-socket IPC you will see `Daemon failed to start` — grant the session the relevant escape (e.g. `--dangerously-bypass-approvals-and-sandbox` or the project-specific override) before retrying.

Use standard file tools (`cat`, `sed`, your edit function) to read and update `.registry/<slug>.md`. Prefer surgical edits to an existing file over rewriting it.

## At the start of every browser task

1. Resolve the origin of the target URL.
2. Compute the slug (see [reference/registry-format.md](./reference/registry-format.md)).
3. `cat .registry/<slug>.md` if it exists. Internalize its gotchas and stable selectors before issuing any commands.
4. Load `reference/*.md` only when a relevant question arises.

## At the end of every browser task

If you learned anything non-obvious, update (or create) the registry entry per [reference/registry-format.md](./reference/registry-format.md). Bump `last_updated` and `visit_count`.

**Intent reminder** (also in [core.md](./core.md) and in each entry's `purpose` frontmatter): entries are agent-facing hindsight, not documentation. Orientation + surprises + speed-ups only. Do **not** inventory the UI. No refs, secrets, or transient content.
