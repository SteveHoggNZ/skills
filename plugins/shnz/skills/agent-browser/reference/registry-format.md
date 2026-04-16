# Site registry format

The site registry is a local folder of per-origin Markdown files under the skill directory:

```
<skill-dir>/.registry/<slug>.md
```

The folder is gitignored — registry knowledge is local to the machine/user that captured it. If a team wants to share entries, copy them manually or maintain a separate, intentionally-committed collection.

## Filename (slug)

Derived from the URL's **origin** (`scheme://host:port`):

1. Drop the scheme (both `http` and `https` collapse to the same file — if you need to distinguish, prefix the slug with `http--` or `https--`).
2. Omit default ports: drop `:80` for http and `:443` for https.
3. Lowercase.
4. Replace `.` and `:` with `-`.
5. Append `.md`.

| URL | Slug |
|-----|------|
| `http://localhost:4173` | `localhost-4173.md` |
| `https://app.example.com` | `app-example-com.md` |
| `https://example.com:8443` | `example-com-8443.md` |
| `http://127.0.0.1:3000/admin` | `127-0-0-1-3000.md` |

Origin is the v1 fingerprint. If two apps share an origin (multi-tenant dev tunnel, reverse proxy multiplexing), extend the slug with a path discriminator: `localhost-4173--admin.md`.

## What belongs in an entry

The lens: **what would a new agent need to know to orient in 30 seconds and not get tripped up?** Entries are high-level. They are not a UI inventory.

Write down:

- **Orientation** — one paragraph: what the app is, the main regions of the screen.
- **Conventions that save time** — e.g. "all nav buttons use `aria-label` matching the displayed text" — one rule that makes dozens of selectors obvious without grepping.
- **Surprises** — things that contradict web defaults or the obvious reading of the UI (login is inline not routed; Enter doesn't submit; a button has no accessible name; an element looks like a link but is a no-op).
- **Stable selectors for genuinely hard-to-rediscover elements** — the message composer, the main action button, auth inputs. Not every button in the nav.
- **Workflows for common tasks** — login, send, search — as short recipes, not full tutorials.

Skip:

- Enumerations of every button or nav item. If a convention covers them, state the convention.
- Things any first snapshot would reveal (element counts, IDs, routine labels).
- Selectors where the element is trivially findable every session (prominent, named, unique).
- Implementation-level detail (class names, CSS variables) unless load-bearing.

Two-minute test: re-read the entry pretending you've never seen the site. If 80%+ of it is "things I'd discover on my first snapshot", it's too long — trim to surprises + speed-ups.

## File structure

A registry entry is YAML frontmatter + Markdown body.

```markdown
---
origin: https://app.example.com
purpose: "Agent-facing orientation + surprises for https://app.example.com. Keep high-level; record only what saves a future agent time or prevents a tripping hazard. Not a UI inventory."
last_updated: 2026-04-17
visit_count: 3
agent_browser_version: 0.25.3
---

# app.example.com

<human-readable title / summary of what this site is, one or two sentences>

## Login

<How to reach the login form, what selectors are stable, where credentials come from. Never embed credentials here.>

## Stable selectors

<CSS selectors that work across sessions for key elements. Refs do not belong here.>

## Gotchas

<Site-specific surprises, numbered or bulleted. Prefer format: "WHAT happens" + "WHY it matters" + "WORKAROUND".>

## Workflows

<Step-by-step recipes for common tasks, in the same shape as reference/patterns.md but specialized for this site.>

## Open questions

<Things you didn't figure out yet. Future sessions can pick these up.>
```

## Frontmatter fields

| Field | Required | Notes |
|-------|----------|-------|
| `origin` | yes | Full origin URL (`scheme://host[:port]`) |
| `purpose` | yes | One-line reminder of what this file is for. Reiterates the registry intent so future agents are primed correctly before reading the body. Template: `"Agent-facing orientation + surprises for <origin>. Keep high-level; record only what saves a future agent time or prevents a tripping hazard. Not a UI inventory."` |
| `last_updated` | yes | ISO date (YYYY-MM-DD) of most recent change |
| `visit_count` | yes | Integer, incremented each time the skill consults this entry for a live task |
| `agent_browser_version` | yes | Version used in the latest confirmed-working session |
| `aliases` | optional | Array of other origins that redirect to / are equivalent to this one |
| `superseded_by` | optional | If this entry has been split/merged, point to the replacement slug |

## Update discipline

Update the entry when you learn something **non-obvious**. Indicators that what you just discovered belongs in the registry:

- You spent more than one snapshot figuring out what to click.
- The element's a11y name differs from its visible label, or has no name at all.
- Default browser/web semantics don't apply (Enter doesn't submit, Tab doesn't move focus the way you expected, etc.).
- You found the stable CSS selector for something that's commonly referenced.
- You confirmed a workflow works end-to-end — promote it to "Workflows".

Do not record:

- Refs (they're stale by the time you save).
- Secrets (passwords, tokens, session cookies).
- Transient content (messages, user names, timestamps from the live page).
- Things already documented in the target site's own docs — link to those instead.

When you update:

1. Change `last_updated` to today.
2. Bump `visit_count` by 1 (only once per session — not per edit).
3. If the CLI version differs from `agent_browser_version` and the session succeeded, update the recorded version.
4. Put new gotchas at the top of the **Gotchas** section (most recently learned = most likely still relevant).
5. When a gotcha is no longer true (site changed, CLI changed), delete it or move it to an **Obsolete** section with a date.

## Writing style

Entries are read by humans and future agent sessions under time pressure. Optimize for scan-ability:

- Lead each gotcha with the observable symptom.
- State the workaround as a concrete command or selector, not prose.
- Keep the entry under ~200 lines. If it grows past that, split it (e.g. `localhost-4173.md` + `localhost-4173--admin.md`).
- Date any claim that might decay ("As of 2026-04-17, the Send button is …").

## Example (sketch)

```markdown
---
origin: https://example.app
last_updated: 2026-04-17
visit_count: 3
agent_browser_version: 0.25.3
---

# example.app — ExampleApp

Kanban board app. Boards on the left, cards in the center, activity rail on the right.

## Selector conventions

- **All toolbar buttons use `aria-label` matching the displayed tooltip** — e.g. `button[aria-label="Add card"]`. Don't grep the snapshot for these.
- **Card bodies have no stable id**; target by visible text within `.board-column [role="article"]`.

## Auth

- Credentials: 1Password item "ExampleApp dev".
- Login is a full route (`/login`) — redirects to `/boards` on success.

## Gotchas

1. **Drag-to-reorder has no keyboard path.** Must use `eval` to call `window.__dnd.moveCard(id, toColumn, toIndex)`.
2. **"Archive" and "Delete" buttons look identical** (both red trash icons, no text). Archive is the outer, Delete is in the confirmation modal that appears after clicking Archive.

## Workflows

### Add a card
1. `click 'button[aria-label="Add card"]'` inside the target column.
2. A `textarea[name="title"]` appears inline. `fill` it, press Enter to confirm.

## Open questions

- Bulk move — is there an API? The UI only supports one card at a time.
```

The example is deliberately short. A real entry for a complex app might be longer, but the trigger for adding a section is always "a future agent would waste time or make a mistake without this", not "it exists".
