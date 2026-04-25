# UI State Debugging

A pattern catalogue for diagnosing state-discrepancy bugs in client-server applications: bubbles stuck spinning, indicators that won't clear, the UI showing different data than the database, screenshots that nobody else can reproduce.

## Why this skill exists

State-discrepancy bugs eat hours because the data is *somewhere correct* and *somewhere wrong* and you have to walk the boundaries to find which one diverged. The mechanics are domain-specific (which DB? which API? which framework's cache?) but the **method** is invariant: walk the layers, verify positively at each one, distrust your own assumptions about which side is right.

This skill is a **pattern catalogue, not a script** (see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md)). Compose its patterns into the diagnosis your specific bug needs. Don't follow it as a checklist top-to-bottom.

## The methodology in one sentence

> Walk the layers in order — DB → API → client cache → render — and stop where the data first goes wrong.

Everything below is depth on the steps of that walk.

## The three layers (load on demand)

[reference/three-layer-verification.md](./reference/three-layer-verification.md) — the core mental model. **Read this one first.** The DB is the source of truth, the API is a computed view, the client cache may be stale, the rendered DOM is the visible artifact. Each boundary is a place data can diverge.

## Patterns the agent draws from

Load these on demand when the relevant pattern matches the bug you're chasing.

### Design / architecture patterns

- [reference/positive-evidence.md](./reference/positive-evidence.md) — prefer "X is closed" responses over "X is not in the open set". Negative evidence is racy when the snapshot pre-dates new arrivals. Bug E v3 (the canonical case study) was exactly this.
- [reference/server-authoritative.md](./reference/server-authoritative.md) — when the server owns a lifecycle (stream open/closed, task pending/done), the client should reflect what the server says, not infer from heuristics. Heuristics that "save the server a round-trip" become wrong-state bugs.
- [reference/synthetic-vs-real-entities.md](./reference/synthetic-vs-real-entities.md) — synthetic IDs (deterministic UUIDs derived from agent+channel, derived stream_ids for atomic messages) need explicit handling. Treating a synthetic ID like a real entity → indicators that never resolve.

### Diagnostic patterns

- [reference/instrumentation-patterns.md](./reference/instrumentation-patterns.md) — when React Devtools isn't enough: `(window as any).__myDebug = []` push pattern for capturing render-loop events, ergonomic dump from console, when to remove the instrumentation.
- [reference/dont-trust-screenshots.md](./reference/dont-trust-screenshots.md) — drive the test yourself. The user's screenshot may be from a stale tab, a different account, an HMR-poisoned bundle. Always reproduce in your own session before declaring success or accepting failure.
- [reference/test-rig-pattern.md](./reference/test-rig-pattern.md) — when a bug is hard to reproduce by hand, scaffold a Playwright rig that creates the conditions, records video, and dumps a structured timeline. The pattern (not a template) for what makes a test rig genuinely useful instead of write-once-throw-away.

### Cache / staleness patterns

- [reference/hmr-context-providers.md](./reference/hmr-context-providers.md) — Vite HMR can't hot-replace React context providers cleanly when their internal hook shape changes. The browser keeps the stale module. Cache-busted reload (`?_b=ts`) or full server restart (kill the port, not just `restart`).
- [reference/cache-snapshot-races.md](./reference/cache-snapshot-races.md) — when API responses contain cached snapshots ("here's the open set as of now") and SSE/WebSockets later deliver new entities, the snapshot is silently wrong for the new arrivals. Either drop the snapshot or make it forward-only.

### Verification patterns

- [reference/known-failure-modes.md](./reference/known-failure-modes.md) — running list of generic anti-patterns the skill has caught. Updated at the end of each diagnostic when a new pattern emerges.

## Per-app registry (read first)

Before any layer walking, identify the origin of the app and load its registry entry.

```
1. Resolve origin: scheme://host:port (e.g. http://localhost:4173)
2. Compute slug: lowercase, replace `.`/`:` with `-`, drop default ports
3. Read .registry/<slug>.md if it exists
```

The registry captures **what previous debugging sessions on this app learned** — false-positive bug shapes (symptoms that look like bugs but are usually correct), framework quirks (HMR stalls, cache caveats), and pointers to where each verification layer's data lives. A known false-positive shape can save the entire investigation.

If no entry exists, you start fresh — and you'll create one before the session ends if anything app-specific was learned.

Format and rules: [reference/registry-format.md](./reference/registry-format.md).

## Procedure (composable, not linear)

The agent picks the steps that match the bug. There is no "step 1, step 2, step 3" — the order depends on which layer you suspect first.

### Step A — Identify the boundary

Where does the user say the bug lives? Map their description to a layer:

- "the database has X but the screen shows Y" → DB↔API or API↔client boundary
- "it works for me but not for them" → client cache or HMR boundary
- "still showing after the fix" → very likely a stale client (HMR or service worker)
- "won't update" → SSE/WebSocket delivery or a cache that isn't invalidated

### Step B — Verify the source of truth

Query the database (or whatever the authoritative store is) directly. This is almost always the cheapest first step.

```bash
# Example shapes — substitute your DB client
psql -c "SELECT … FROM <table> WHERE <key> = '<id>';"
redis-cli GET <key>
sqlite3 <db> "SELECT …"
```

If the DB disagrees with the user's description, the bug is in your understanding, not the system. Re-read the user's report.

If the DB matches the user's description (the data is genuinely wrong there), the bug is upstream of the DB — in the writer. Stop walking the read path; investigate the write path.

### Step C — Verify the API response

Hit the API directly with `curl`. Compare the response to what the DB says.

```bash
curl -s -H "Authorization: …" http://localhost:port/api/… | jq .
```

If the API disagrees with the DB → bug is in the read handler, the cache layer between them, or the response shape (a field the client expects is missing or differently-named).

If the API agrees with the DB → walk further to the client.

### Step D — Verify what the client received

The client may have cached an older response. Inspect what it currently *thinks* the data is, not what the API would return if asked fresh.

In a React app:
- Add `(window as any).__myDebug` instrumentation in the relevant component (see [reference/instrumentation-patterns.md](./reference/instrumentation-patterns.md))
- Reload, reproduce, dump from the browser console
- Compare to the API response

If the client has stale data → cache invalidation bug, or the SSE/WebSocket missed an event, or a snapshot-race (see [reference/cache-snapshot-races.md](./reference/cache-snapshot-races.md)).

### Step E — Verify what's rendered

The DOM is the visible artifact. If the client's data is correct but the DOM shows wrong, the bug is in the render pipeline (a memo'd component holding stale props, a derived state that didn't recompute, a status field set somewhere unexpected).

This step is where "the user's screenshot says X but the bug is fixed" gets resolved — usually the user's *bundle* is stale, not their data. See [reference/dont-trust-screenshots.md](./reference/dont-trust-screenshots.md).

### Step F — Reproduce yourself

Before declaring fixed, reproduce in your own session. If the user is on a long-lived browser tab, they may be running a stale JS bundle even after `Cmd-R`. Drive the test via a fresh-context tool (agent-browser, Playwright) to verify the fix in clean conditions.

When the bug only reproduces under specific conditions (timing, state setup), build a test rig — see [reference/test-rig-pattern.md](./reference/test-rig-pattern.md).

### Step G — Update the registries

Three update channels — pick the right one for what you learned:

- **App-specific learnings** (a new false-positive shape on this app, a framework quirk that bit you, a layer pointer that wasn't in the entry yet) → update `.registry/<slug>.md`. Bump `last_updated` and `visit_count`.
- **Generic anti-patterns** (the root cause was a shape that could exist in another codebase — "negative-evidence cache seed", "context provider HMR stall", "synthetic ID treated as real entity") → append to [reference/known-failure-modes.md](./reference/known-failure-modes.md). One line.
- **Codebase-specific findings** (this project's file layout, exact commands, project-specific bugs) → **repo-local skill** in `<repo>/.claude/skills/`. Don't pollute the registry with these — the registry should still be accurate if the codebase were rewritten.

See [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) for the resource matrix.

## Pairing with tool skills

This skill provides methodology. The actual driving needs a tool skill:

- [`agent-browser`](../agent-browser/) — load it for the "verify what the client received" and "reproduce yourself" steps. Provides the persistent registry of how to log into and navigate each site.
- A repo-local skill that knows the project's file layout — load it for the specific commands at each layer (which DB query? which API endpoint? which UI component?).

The agent's job is to recognise that this skill (methodology) plus those skills (tools) together cover the diagnosis. Don't expect this skill to know the AMP message_streams schema or the agent-browser CLI flags — that's the partner skills' job.

## Anti-patterns (things this skill is *against*)

- **Symptom-chasing.** Adding `setTimeout(retry, 5000)` because the bug is intermittent. Fix the root cause; symptoms cluster around real problems.
- **Cargo-cult cache-busting.** Adding `?v=${Date.now()}` to every fetch is not a fix. Find why the cache had the wrong data.
- **"Defensive" defaults.** A heuristic that hides the bug ("if status is null, treat as closed") is the same shape as the ghost-buster bug we caught — it makes wrong-state look right and breaks at the seams. Surface unknowns; don't paper over them.
- **Believing the screenshot.** It is one observer's view at one moment in one bundle. Reproduce.

## See also

- [reference/three-layer-verification.md](./reference/three-layer-verification.md) — the mental model
- [reference/known-failure-modes.md](./reference/known-failure-modes.md) — running list
- [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) — how this skill fits with tool/procedure skills
