# Positive evidence

Design pattern for state APIs: return *what is true*, not *what isn't false*.

## The anti-pattern

A common API shape returns the "current open set" and lets the client infer everything else:

```http
GET /entities

{
  "entities": [{"id": "a", …}, {"id": "b", …}, {"id": "c", …}],
  "open_ids": ["a"]
}
```

Client code interprets this as: "anything in `entities` that isn't in `open_ids` is closed." Looks reasonable.

It's racy. Specifically, it's racy at the moment a *new* entity arrives via real-time delivery (SSE, WebSocket, polling) **after** the snapshot was computed.

Imagine the timeline:

```
t=0   GET /entities returns { entities: [], open_ids: [] }
       Client caches: entities=[], open_ids=[]
       (nothing wrong yet — no entities)

t=1   Server creates entity "a" (open)

t=2   SSE delivers entity "a" to client
       Client merges into entities cache: entities=[{a, …}]
       open_ids cache untouched: still []

t=3   Client renders. Asks "is 'a' in open_ids?"
       NO → client labels 'a' as CLOSED.
       Wrong.
```

The cached `open_ids` was correct *at the moment of fetch* but is silently wrong for any entity created after t=0. The client has no way to know which entities were "covered" by the snapshot and which arrived later.

## The fix: positive evidence

Return what is true, not what isn't false:

```http
GET /entities

{
  "entities": [{"id": "a", …}, {"id": "b", …}, {"id": "c", …}],
  "closed_ids": ["b", "c"]
}
```

Client interprets: "anything in `closed_ids` is closed; anything not in the list is unknown / still open."

The `closed_ids` field is *forward-only* — once an id is closed, it stays closed (or at least, the assumption is monotonic in the direction you care about). When a new entity arrives via SSE that wasn't in `closed_ids`, the client correctly leaves its status undefined ("still open" until proven otherwise).

The server can later push a `closed` event for that entity, and the client maps it to the same field. Now there's one source of truth (closure events) instead of two (the snapshot AND the events disagreeing).

## The principle

> Negative evidence ("X is not in my list of …") is brittle when the list is a stale snapshot. Positive evidence ("X is definitely closed") is robust to staleness.

In design terms: **prefer monotonic, forward-only signals**. They compose cleanly with real-time event streams. Snapshots that you have to *invert* to extract meaning are race-bombs.

## Recognising the pattern in the wild

Smells that you have a negative-evidence API:

- The response contains an `open_*` / `active_*` / `current_*` array.
- Client code does `if (!openSet.has(id)) treatAsClosed(id)`.
- The bug report is "things flicker between open and closed", or "this only happens when the page loads at a specific moment", or "this only happens on slow connections".

Fix shape:

- Server adds a positive-evidence field (`closed_*`, `done_*`, `failed_*`) computed from the same data.
- Client switches to seeding from the positive field. The negative field can stay for back-compat but client code should not use it for inference.
- For phantom IDs (synthetic IDs that never have a real lifecycle row — see [synthetic-vs-real-entities.md](./synthetic-vs-real-entities.md)), the server should detect their absence and include them in the positive-evidence list ("no row exists, so the entity is logically closed").

## When this pattern is the wrong fix

Sometimes the snapshot really *is* the source of truth and there's no real-time event stream. In that case, just refetch on every render boundary — the bug isn't the API shape, it's that the client is treating a one-shot fetch as a subscription. Reach for positive evidence when there's a SSE/WebSocket/polling stream alongside.

## Case study

This pattern was the root cause of "Bug E v3" in the AMP repo's activity-indicator investigation. The response had `open_streams: []` (empty because the initial fetch happened before any agent activity); SSE later delivered entries with stream_ids; the client marked all of them as closed because they weren't in the stale `open_streams` list. Symptom: every agent bubble flipped to a green checkmark the moment the agent posted its first reasoning entry.

The fix was a one-field rename + invert the semantics: `closed_streams: []` returned by the server, client seeds only that. Took longer to *see* the bug than to fix it.
