# Three-layer verification

The mental model. Read this before any other reference file.

## The layers

Every client-server app has at least four levels where state lives, each potentially out of sync with the others:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Source of truth (DB / persistent store)                  │
│    What is actually stored. Authoritative.                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ read handlers, queries, RLS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Server response (computed view)                          │
│    What the API returns when asked. May filter, transform,  │
│    or aggregate. May contain cached snapshots.              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE / WebSockets
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Client cache (React Query, Apollo, Redux, refs)          │
│    What the client *currently believes*. May be stale,      │
│    racy with later real-time events, or differently-shaped  │
│    than the API response if a transform layer ran.          │
└──────────────────────────┬──────────────────────────────────┘
                           │ React render, derived state, memo
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Rendered DOM (the visible artifact)                      │
│    What the user actually sees. May lag the cache if a      │
│    component is memo'd against stale props or a derived     │
│    value didn't recompute.                                  │
└─────────────────────────────────────────────────────────────┘
```

A state-discrepancy bug is, by definition, two adjacent layers disagreeing. The diagnostic question is **which two**.

## How to walk the layers

Pick the **cheapest** verification that pins down where the data first goes wrong. Usually that's the DB — one SQL query, no auth dance, no rendering.

### 1. DB

Query the source of truth directly.

```bash
psql -c "SELECT id, status, updated_at FROM <table> WHERE <key> = '<id>'"
```

If the DB shows the *wrong* value (matches what the user is complaining about), the bug is upstream — in the writer. Investigate the write path. The read path is a red herring.

If the DB shows the *right* value, the disagreement is downstream. Continue.

### 2. API

Hit the read endpoint with `curl`.

```bash
curl -s -H "Authorization: …" 'http://host/api/…' | jq .
```

Compare the response shape and values to the DB.

If the API response disagrees with the DB:
- A response transform may be dropping or mutating a field.
- The response may contain a *cached snapshot* (e.g. an `open_streams: []` list computed at one moment) that's stale relative to other fields in the same response.
- An RLS / permission layer may be filtering rows.
- The handler may be returning data from a read replica that hasn't caught up.

Stop here and fix the API layer.

If the API response matches the DB, continue.

### 3. Client cache

The client may have cached an older response and not re-fetched. To inspect:

- Add a temporary `(window as any).__myDebug` instrumentation in the relevant component (see [instrumentation-patterns.md](./instrumentation-patterns.md)).
- Or open React Devtools and walk the relevant context provider's value.
- Or check the React Query devtools panel for the cached query.

Compare the cached value to what `curl` just returned.

If they disagree:
- The cache may not have been invalidated when the data changed (no SSE/WebSocket event, or the event handler dropped it).
- A stale snapshot may have been cached at one time and never overwritten (snapshot-race — see [cache-snapshot-races.md](./cache-snapshot-races.md)).
- The transform from API response to cache shape may be lossy or buggy.

If they agree, continue.

### 4. Rendered DOM

What's actually painted may differ from the cache if a component is memo'd against stale props or a derived value didn't recompute when its inputs changed.

Inspect the DOM directly (not React Devtools — actual `document.querySelector`):

```js
document.querySelectorAll('[data-message-id]').forEach(el => {
  console.log(el.dataset.messageId, el.querySelector('svg[aria-label]')?.ariaLabel)
})
```

If the DOM disagrees with the cache, the bug is in the render pipeline:
- A memo'd parent isn't re-rendering when a child's status changed.
- A derived value (`useMemo`) has stale dependencies.
- A status field is being computed from the wrong source (e.g. from `event.type` instead of from the current cache entry).

If they agree — and the user *still* says it's wrong — see [dont-trust-screenshots.md](./dont-trust-screenshots.md). The user's bundle may be stale.

## The first-divergence rule

**Always identify the *first* layer where the data is wrong.** Fixing a downstream symptom while leaving the upstream cause in place produces a fix that breaks again the next time the same path is exercised.

Example: if the DB is correct, the API is wrong, and the client is wrong (because it faithfully reflects the wrong API response), fix the API. Don't add a client-side workaround.

## When to skip layers

You can skip the DB step IF:

- You already have strong evidence the data exists correctly somewhere (e.g. another agent's log line shows a successful write).
- The bug is clearly a UI-render issue (the same data renders correctly in another tab right now).

You can skip the API step IF:

- The client cache directly shows wrong data and the question is "why didn't the cache get updated".

Don't skip the **client cache** step when investigating "the UI is stuck on old data" — this is almost always where the bug lives.

## Recording your findings

Once the bug is localised to a specific layer:

- **Generic anti-patterns** (snapshot-race, negative-evidence-cache, HMR-context-stale) → append to [known-failure-modes.md](./known-failure-modes.md).
- **Codebase-specific findings** → repo-local skill in `<repo>/.claude/skills/`. Don't pollute generic skill references with project file paths.

See [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) for the resource matrix.
