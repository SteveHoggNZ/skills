# Agent Browser

Drive any web UI with the `agent-browser` CLI — a daemon-backed browser automation tool — and a persistent per-site registry that captures hard-won knowledge (stable selectors, gotchas, tested workflows) so each subsequent session on the same site is faster and less error-prone.

## Why this skill exists

`agent-browser` on its own is fast but stateless: every session rediscovers the same quirks (this input is `contenteditable`, Enter creates a newline instead of submitting, that close button has no accessible name, the wait-for-selector will hang for 2.5 minutes if the selector is wrong). Those lessons are lost.

This skill wraps the CLI with a **site registry** — a local, gitignored folder of Markdown notes keyed by origin — so that knowledge accumulates across sessions.

## Registry intent (read before writing entries)

The `.registry/` folder is **agent-facing hindsight**, not documentation. Its single purpose: let a future agent orient on a site in ~30 seconds and avoid tripping on known surprises.

What belongs in an entry:

- **Orientation** — one paragraph describing what the app is and the main regions of the UI.
- **Conventions that save time** — "all nav buttons use `aria-label` matching the displayed text" beats a list of 12 individual selectors.
- **Surprises and gotchas** — things that contradict web defaults or the obvious reading of the UI. These are the highest-value content.
- **Stable selectors for hard-to-rediscover elements** — the message composer, the primary action button, auth inputs. Not every nameable button.
- **Short workflow recipes** for common tasks (login, send, search).

What does **not** belong:

- UI inventories — every button, every nav item, every region in exhaustive detail.
- Anything a first snapshot would trivially reveal.
- Implementation detail (class names, CSS variables) unless load-bearing.
- Secrets, ephemeral refs, transient content.

Two-minute test when writing or reviewing an entry: re-read it pretending you've never seen the site. If most of it is "things I'd discover in one snapshot anyway", trim aggressively. Keep only surprises and speed-ups.

This is reiterated in every entry's `purpose` frontmatter field. Honor it on every update.

## Procedure

### 1. Identify the site

From the target URL, extract the **origin** (`scheme://host:port`) and compute a filename slug:

- `http://localhost:4173` → `localhost-4173.md`
- `https://app.example.com` → `app-example-com.md`
- `https://example.com:8443` → `example-com-8443.md`

Slug rules: lowercase, replace `.`/`:` with `-`, drop the scheme (both http and https map to the same file — if you need to distinguish, prefix with `http--` or `https--`). Omit default ports (`:80`, `:443`).

Origin is the v1 fingerprint. If two distinct apps share the same origin (e.g. dev-tunnel multiplexing), extend the slug with a path prefix discriminator.

### 2. Load existing site knowledge

Before issuing any browser command, check for an existing registry entry. The registry folder is **co-located with this skill's files** — it is NOT in the project CWD. Locate it relative to this `core.md` file:

```
<skill-dir>/.registry/<slug>.md
```

For example, if this skill is installed at `/Users/alice/.copilot/installed-plugins/shnz-skills/.../agent-browser/`, the registry lives at `.../agent-browser/.registry/<slug>.md`. Do **not** create or read `.registry/` relative to the project working directory.

If it exists, **read it in full**. It contains:

- Login flow (selectors, credentials source)
- Stable CSS selectors for key elements
- Site-specific gotchas
- Tested workflows (step-by-step)
- Last-updated timestamp and visit count

If it does not exist, you start fresh — and you will create one before the session ends.

### 3. Load generic references as needed

This skill ships three reference files under `reference/`. Read them on demand, not upfront:

- [reference/commands.md](./reference/commands.md) — CLI syntax, flags, return values
- [reference/gotchas.md](./reference/gotchas.md) — generic gotchas that apply to any site
- [reference/patterns.md](./reference/patterns.md) — login, form fill, wait strategies, chaining, screenshots, video, JS eval

Load `commands.md` when you need syntax you don't remember. Load `gotchas.md` when something unexpected happens. Load `patterns.md` when building a multi-step workflow.

### 4. Execute the task

Run `agent-browser` commands to accomplish the user's goal. Key operating principles (spelled out in detail in the reference files):

- **Always `--interactive` first.** `agent-browser snapshot --interactive` returns only buttons/inputs/links — fast scan for what to click. Fall back to full snapshot for structural context.
- **Refs are ephemeral.** After any DOM-changing action (click, fill, navigate) re-snapshot before referencing an element.
- **Chain for speed.** `cmd1 && cmd2 && cmd3` in a single shell call avoids tool round-trips.
- **Never hardcode a ref across sessions.** Record stable CSS selectors in the site registry instead.

#### Session-scoped command file

Do not invoke `npx agent-browser` directly from the shell — build a session-scoped command file and run it.

**At the start of each session**, pick ONE unique command-file path and reuse it for every invocation in that session. Recommended shape:

```
/tmp/ab-cmd-<YYYYmmddHHMMSS>-<4-char-random>.sh
```

Include the current time-to-second plus 4 random hex chars so two sessions starting in the same second still get distinct paths. Once picked, **don't change it for the rest of the session** — every Write step in the session rewrites that same path, every Bash step invokes it.

Per step:

1. Overwrite the session's command file. Include shebang, `set -euo pipefail`, and the `npx agent-browser` call(s); chain multi-step with `&&`.
2. Execute: `bash <session-cmd-path>`.

Why this shape:

- **Approval-friendly per session.** The invocation signature — `bash <session-cmd-path>` — is identical across every step within a session. Claude-Code-style exact-command approvals match once per session and cover the rest.
- **No intra-session race.** Tool calls in one session are sequential, so reusing one path within a session is safe.
- **No cross-session race.** Two sessions starting concurrently pick distinct suffixes, so their command files can't collide.

If you want one approval across **all** future sessions, add a wildcard rule to Claude Code's settings.json:

```json
"permissions": {
  "allow": ["Bash(bash /tmp/ab-cmd-:*)"]
}
```

See [reference/patterns.md](./reference/patterns.md) for example command files.

### 5. Capture new knowledge

Whenever you learn something **non-obvious** about the site, update the registry entry. See [reference/registry-format.md](./reference/registry-format.md) for the exact format.

Triggers to update the registry:

- A selector you had to discover by experiment (not from a label on the page)
- A behavior that contradicts default web semantics (e.g. Enter in a rich-text editor creates a newline)
- An element whose name/role in the a11y tree is different from what its visible label implies
- A successful multi-step workflow worth replaying (login sequence, "create X" flow)
- A confirmed dead-end (e.g. "the Settings button at ref Xxx looks like a link but is a no-op unless Y is true")

Do **not** record:

- Specific ref values (they change every snapshot — useless next session)
- One-time content (message text, temporary state)
- Things anyone would discover by reading the page's HTML source

Every update bumps `last_updated` and `visit_count` in the frontmatter.

### 6. Create the registry entry if missing

If no `.registry/<slug>.md` existed at step 2 and you learned anything worth keeping in step 5, create it now. At minimum capture: the origin, the date, the `agent-browser` version (from `npx agent-browser --version` if not already known), and whatever you learned. The registry directory `.registry/` is gitignored and will be created on first write.

## Minimum viable session

A trivial session that touches a known site looks like:

1. Read `.registry/<slug>.md` (if present).
2. Run browser commands.
3. If nothing new was learned, end. Otherwise update the entry.

A trivial session on an unknown site adds a final step: create the entry.

## Version assumptions

This skill was written against `agent-browser` 0.25.x. If you encounter a command that's documented here but rejected by the CLI, check `npx agent-browser --help` and note the version drift in the site registry's frontmatter.
