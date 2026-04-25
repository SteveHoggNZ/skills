# Debugging-registry format

The registry is a local folder of per-origin Markdown files inside the skill:

```
ui-state-debugging/.registry/<slug>.md
```

The folder is gitignored — registry knowledge is local to the machine that captured it. Each entry records **debugging quirks for one application**: false-positive bug shapes, framework-level gotchas, app-specific layer pointers — anything a future debugging session on the same app would benefit from skipping the rediscovery of.

This is a **complement to**, not a replacement for, [`agent-browser`'s registry](../../agent-browser/reference/registry-format.md). Both can coexist on the same origin; they capture different things.

## Filename (slug)

Same scheme as `agent-browser`'s registry — derived from the URL's **origin** (`scheme://host:port`):

1. Drop the scheme (both `http` and `https` collapse).
2. Omit default ports (drop `:80` / `:443`).
3. Lowercase.
4. Replace `.` and `:` with `-`.
5. Append `.md`.

| URL | Slug |
|-----|------|
| `http://localhost:4173` | `localhost-4173.md` |
| `https://app.example.com` | `app-example-com.md` |
| `https://example.com:8443` | `example-com-8443.md` |

Sharing the slug scheme with agent-browser means a debugger entry and a driver entry for the same app are obviously paired by filename.

## What belongs in an entry

The lens: **what would a future agent debugging a state-discrepancy bug on this app need to know to skip relearning?** Entries are high-level — about *the app's debugging behaviour*, not its features.

Write down:

- **Orientation** — one short paragraph: what the app's frontend is built on (React + Vite + TanStack Query? Next.js + Apollo? Plain HTML + HTMX?), where its backend lives, where it stores state.
- **Layer pointers** — the names of the things at each verification layer: which DB tables hold the lifecycle state, which API endpoints return it, which client cache keys / context providers own the rendered version. Names, not commands. Codebase-specific commands belong in a repo-local skill.
- **Known false-positive bug shapes** — symptoms that *look* like bugs but are usually correct ("indicators that spin for >5 minutes are usually fine — this app's agents legitimately run that long"). Saves wasted investigation.
- **Framework-level debugging quirks** — "this app's HMR can't replace XContext cleanly", "service worker caches the bundle on `/`", "WebSocket reconnects drop a stream_status: closed event silently". The kind of thing that bites you once and you wish you'd known going in.
- **Pairings** — links to the corresponding `agent-browser` registry entry, the repo-local skill, or the project's runbooks. So a future agent loads them together.

Skip:

- Architecture documentation (lives in the codebase).
- Specific commands, file paths (lives in the repo-local skill).
- Bug postmortems with full timelines (lives in the project's `findings.md` or similar).
- Anything that's not specific to **debugging on this app**.

Two-minute test: re-read the entry pretending you've never debugged this app. If most of it is "things I could find by reading the codebase", trim. Keep only the speed-ups and the gotchas.

## File structure

A registry entry is YAML frontmatter + Markdown body.

```markdown
---
origin: http://localhost:4173
purpose: "Agent-facing debugging quirks for http://localhost:4173. Surprises and false-positive bug shapes; not architecture documentation."
last_updated: 2026-04-26
visit_count: 1
agent_browser_registry: localhost-4173.md  # link to the paired entry
repo_skill: amp-stream-bubble-diagnostics  # link to the repo-local skill
---

# localhost:4173 — AMP UI

## Orientation

React + Vite + TanStack Query + TanStack Start. Server is Go on port 8081. State lives in PostgreSQL `message_streams` (lifecycle) and `channel_entries` (events). Client mirrors via SSE on `/api/stream/entries`.

## Layer pointers

- **DB**: `public.message_streams` (lifecycle), `public.channel_entries` (events).
- **API**: `GET /api/v2/channels/{id}/entries` returns `closed_streams[]` (positive evidence — see `reference/positive-evidence.md`). SSE events on `/api/stream/entries` carry `stream_status` updates.
- **Client cache**: `EntriesStreamContext` (React context, holds `streamStatusMapRef`). `useEntries` (React Query, holds the entries cache).
- **Render**: `EntryGroupContainer.foldGroupToMessage` derives bubble status. The "Master Switch" pattern: `group.isClosed → status='sent'`.

## Known false-positive bug shapes

- **Indicators spinning >5 minutes**: usually correct. This app's coordinator agents (e.g. Werewolf GM) legitimately run for tens of minutes between user actions. The bubble accurately reflects "agent is still working." Don't chase this unless the corresponding stream is actually closed in the DB.

## Framework debugging quirks

- **HMR can't replace `EntriesStreamContext` cleanly.** Editing this file requires a cache-busted reload (`?_b=ts`) — plain `Cmd-R` keeps the stale provider in the React tree. See `reference/hmr-context-providers.md`.
- **Atomic `/messages` send produces synthetic stream_ids**: deterministic UUIDv5 with no `message_streams` row. The API correctly classifies these as closed via the `closed_streams` query (LEFT JOIN finds no row → marked closed). See `reference/synthetic-vs-real-entities.md`.

## Pairings

- `agent-browser` registry: `localhost-4173.md` (login flow, DOM selectors, channel creation workflow).
- Repo-local skill: `<repo>/.claude/skills/amp-stream-bubble-diagnostics/` (DB queries, log paths, restart commands).
- Findings doc: `<repo>/.ai/plans/improve_activity_indicators/findings.md` (history of Bug E v1/v2/v3).
```

## Lifecycle

- **Load**: at the start of every diagnostic session, resolve the origin of the app being debugged and read `.registry/<slug>.md` if it exists. Internalize the orientation, layer pointers, and known false-positives before starting investigation.
- **Update**: at the end of the session, if you discovered a new framework quirk or false-positive shape, append to the entry. Bump `last_updated` and `visit_count`.
- **Don't pollute**: codebase-specific findings (commands, exact file paths, project-specific bugs) go in the **repo-local skill**, not here. The registry is for things that would still be true if the codebase were rewritten in a different language.

## Why this is separate from agent-browser's registry

Different invocation mode, different content shape:

- `agent-browser/.registry/<slug>.md` is loaded by `agent-browser` whenever the agent drives the UI. Content: how to *interact* with the app (selectors, login, workflows).
- `ui-state-debugging/.registry/<slug>.md` is loaded by `ui-state-debugging` whenever the agent is diagnosing a state bug on the app. Content: how to *debug* the app (false-positive shapes, framework quirks, layer pointers).

Co-locating them in one file would force every browser-driving session to load the debugging quirks (mostly irrelevant) and every debugging session to load the selector inventory (mostly irrelevant). Keeping them separate keeps each registry tight and on-topic.

The two entries link to each other in their `agent_browser_registry` / `paired_debug_registry` frontmatter fields, so a future agent always knows the other exists.
