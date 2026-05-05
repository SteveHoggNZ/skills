---
name: agent-browser
kind: procedure
max_recording_seconds: 120
description: "Drive any web UI with the agent-browser CLI and a persistent per-site registry of selectors, gotchas, and workflows that accumulates across sessions. Use when the user asks to navigate a site, click, fill forms, take a screenshot, record, scrape, or automate/test a webpage — trigger phrases include 'go to [url]', 'click on', 'fill the form', 'take a screenshot', 'scrape', 'automate', 'test the website', 'log into'."
---

<!-- Claude Code adapter — the canonical procedure lives in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Claude Code specifics

The session-scoped command-file invocation pattern is defined in [core.md](./core.md) — follow that verbatim. This section is only the Claude-Code-specific tool/permission delta.

- **`Bash` always passes `dangerouslyDisableSandbox: true`.** The `agent-browser` daemon uses a Unix socket that the sandbox blocks, producing `Daemon failed to start` otherwise.
- **Tool mapping**:
  - `Write` → overwrite the session's `/tmp/ab-cmd-<…>.sh` file per step; create `.registry/*.md` entries on first write.
  - `Bash` (sandbox disabled) → only to run `bash /tmp/ab-cmd-<…>.sh`.
  - `Read` → existing `.registry/*.md` entries and `reference/*.md` files.
  - `Edit` → partial updates to existing registry entries (preferred over `Write`).
  - `Grep` / `Glob` → searching the registry for related origins.
- **One approval across all sessions (optional).** Add to Claude Code `settings.json`:
  ```json
  "permissions": { "allow": ["Bash(bash /tmp/ab-cmd-:*)"] }
  ```

## At the start of every browser task

1. Resolve the origin of the target URL.
2. Compute the slug (see [reference/registry-format.md](./reference/registry-format.md)).
3. Read `.registry/<slug>.md` if it exists. If it does, internalize its gotchas and stable selectors before issuing any commands — this is where the "enhanced" in the skill name comes from.
4. Only load `reference/commands.md`, `reference/gotchas.md`, `reference/patterns.md` when relevant.

## At the end of every browser task

If you learned anything non-obvious, update (or create) the registry entry per [reference/registry-format.md](./reference/registry-format.md). Bump `last_updated` and `visit_count`.

**Intent reminder** (also in [core.md](./core.md) and in each entry's `purpose` frontmatter): registry entries are agent-facing hindsight, not documentation. Record orientation, surprises, conventions that save time, and stable selectors for hard-to-rediscover elements. Do **not** inventory the UI. Do not record refs, secrets, or transient content. If most of what you're writing is "things a first snapshot would reveal", trim.
