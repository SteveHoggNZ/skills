# Render-stability registry format

The registry is a local folder of per-origin Markdown files inside the skill:

```
ui-render-stability/.registry/<slug>.md
```

The folder is gitignored — registry knowledge is local to the machine that captured it. Each entry records **app-specific render-stability quirks**: components known to mount/unmount, conditional-render patterns the app overuses, parts of the codebase known to be CLS-heavy.

This is a **complement to** the [`agent-browser`](../../agent-browser/reference/registry-format.md) and [`ui-state-debugging`](../../ui-state-debugging/reference/registry-format.md) registries. All three can coexist on one origin; they capture different aspects:

- `agent-browser/.registry/<slug>.md` — "how to *drive* this site" (selectors, login, workflows)
- `ui-state-debugging/.registry/<slug>.md` — "how to *debug state issues on* this site"
- `ui-render-stability/.registry/<slug>.md` — "how to *make this site visually stable*"

## Filename (slug)

Same scheme as the other registries — derived from the URL's **origin** (`scheme://host:port`):

| URL | Slug |
|-----|------|
| `http://localhost:4173` | `localhost-4173.md` |
| `https://app.example.com` | `app-example-com.md` |

Sharing the slug scheme means all three registries for the same app are obviously paired by filename.

## What belongs in an entry

The lens: **what would a future agent diagnosing a render-stability bug on this app benefit from skipping the rediscovery of?**

Write down:

- **Orientation** — one paragraph: framework (React + Vite + TanStack Start? Next.js? plain HTML?), state management (React Query? Apollo?), routing model.
- **Known conditional-chrome patterns** — components in this app that are known to mount/unmount based on data state. Name the components and describe the trigger condition. ("`TabStrip` mounts only when `channel.frames.length > 0`. Empty channels → no tabs.")
- **Known cascade triggers** — actions that invalidate broad cache slices. ("Channel rename invalidates all `['channel', id]` keys.")
- **Skeleton state coverage** — which routes/components have proper skeleton states; which fall back to `null`-during-loading. ("Channel timeline has skeleton; channel inspector does not.")
- **App-specific layout primitives** — components or utilities that exist for layout stability. ("`<StableHeight>` wrapper preserves min-height during async swaps.")

Skip:

- Architecture documentation (lives in the codebase).
- Specific commands, file paths (lives in the repo-local skill).
- Generic CSS / React anti-patterns (lives in `reference/known-anti-patterns.md`).

## File structure

```markdown
---
origin: http://localhost:4173
purpose: "Agent-facing render-stability quirks for http://localhost:4173. Conditional-chrome patterns and cascade triggers; not architecture documentation."
last_updated: 2026-04-26
visit_count: 1
agent_browser_registry: localhost-4173.md
ui_state_debugging_registry: localhost-4173.md
repo_skill: amp-stream-bubble-diagnostics
---

# localhost:4173 — AMP UI

## Orientation

React + Vite + TanStack Query + TanStack Start (file-based router). State managed via TanStack Query for server state and a few React contexts (`EntriesStreamContext`, `WorkspaceContext`) for client state.

## Known conditional-chrome patterns

- **Top tab strip** (`apps/ui/src/routes/index.tsx` ~line 2297) renders Application/Canvas/Workflow/Messages tabs conditionally. Specifically: `WorkflowTab` only mounts when a workflow manifest frame exists in the channel; `MessagesTab` mounts based on entry count. Empty channels show NO tab strip → flash on first message arrival.
- **Right inspector panel** swaps between two components: `<ChannelInspector>` (when no specific entity selected) and `<EntityInspector>` (when an entry is selected). Different sizes → CLS.
- **`Assistant` button in header** appears when `?assistant=true` query param is set; mounts/unmounts on toggle.

## Known cascade triggers

- **Channel rename** → invalidates `['channel', id]` cache key. All channel-scoped components re-render.
- **New entry arrival via SSE** → invalidates `['entries', channelId]` first page. Adjacent components (sidebar unread badge, channel header timestamp) also re-render.

## Skeleton state coverage

- **Channel timeline** (`<EntriesTimeline>`) has skeleton placeholders matching final layout — good.
- **Channel inspector** does NOT have a skeleton; renders `null` during initial fetch, then snaps to populated state. Source of perceived flash on channel switch.
- **Sidebar channel list** has no skeleton; arrives all at once on first load. Acceptable because subsequent loads are cached.

## Pairings

- `agent-browser` registry: `localhost-4173.md`.
- `ui-state-debugging` registry: `localhost-4173.md`.
- Repo-local skill: `<repo>/.claude/skills/amp-stream-bubble-diagnostics/`.
```

## Lifecycle

- **Load**: at the start of every render-stability diagnostic, resolve the origin and read `.registry/<slug>.md`. Internalize known conditional-chrome and cascade patterns before extracting frames.
- **Update**: at the end of the session, append any new app-specific patterns. Bump `last_updated` and `visit_count`.
- **Don't pollute**: codebase-specific findings (exact file paths, exact line numbers, project-specific bugs) go in the **repo-local skill**, not here. The registry is for things that would still be true if the codebase were rewritten in a different language but kept the same UX.

## Why this is separate from the other registries

Different content shape, different load triggers:

- `agent-browser` loads when driving the UI; cares about selectors and workflows.
- `ui-state-debugging` loads when state is wrong; cares about layer pointers and false-positive bug shapes.
- `ui-render-stability` loads when the UI is visually unstable; cares about conditional-chrome patterns and cascade triggers.

Co-locating them in one file would force every browser-driving session to load the render-stability quirks (mostly irrelevant) and vice versa. Keeping them separate keeps each registry tight and on-topic. They cross-reference in the frontmatter so a future agent always knows the others exist.
