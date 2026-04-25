# Cache snapshot races

Bug shape: an API response embeds a cached snapshot field (a list of currently-active items, a "last updated" timestamp, a count). The client caches the response. Later, real-time events deliver new items that weren't in the snapshot. The cached snapshot is silently wrong for those new items, and any client logic that consults the snapshot to classify them gives wrong answers.

## The mechanism

```
t=0   GET /api/things returns:
        {
          things: [...existing items...],
          active_ids: ["a", "b"]   ← snapshot of "what's currently active"
        }
      Client caches the whole response.

t=1   SSE delivers a new thing "c" (active).
      Client merges it into things[]: things=[a, b, c].
      Client does NOT update active_ids (no event for it).
      active_ids cache is still ["a", "b"] — stale.

t=2   Client renders, asks "is 'c' active?"
      Looks up: 'c' in active_ids? NO.
      Renders 'c' as inactive. Wrong.
```

The client's cache merged correctly for `things[]` (item-level updates) but not for `active_ids` (which would need its own event stream to stay current). The snapshot was correct *for the moment of fetch* but is silently wrong for any item arriving later.

## Why this is so common

It feels natural to embed snapshot fields in API responses:

- Saves round-trips ("here's everything you need to render").
- Looks self-contained ("the response is internally consistent at this moment").
- Common in REST conventions (`?include=` / `_embed=` patterns, GraphQL resolvers).

The trap is that the response is consumed by a *long-lived* client that mixes the snapshot with subsequent real-time events. The snapshot was a one-shot; the events are a stream; mixing them produces wrong-state.

## The fixes

Three options, from cheapest to most invasive:

### Option 1: Drop the snapshot field

If the client doesn't strictly need it, just remove it from the response. Force the client to compute everything from the per-item data and the event stream.

This is often the cleanest fix. The snapshot was an optimisation, not a primitive.

### Option 2: Invert to positive evidence

Change the snapshot to a *forward-only* set: instead of "currently active" (which silently goes stale for new items), return "explicitly closed" (which is monotonic — a closed item stays closed).

See [positive-evidence.md](./positive-evidence.md) for the full pattern. This was the fix for Bug E v3 in the AMP investigation.

### Option 3: Refetch when the snapshot is needed

If the snapshot represents a global aggregate that's expensive to maintain client-side, refetch the snapshot on demand instead of caching it. Trade-off: adds round-trips.

This is the right choice when the snapshot is genuinely a server-computed view (e.g. "total count of unread messages across all channels") that the client has no way to reconstruct from per-item events alone.

### Option 4: Add a snapshot event stream

For each snapshot field, define a corresponding real-time event so the snapshot stays current alongside the per-item events. (`active_ids_changed: { added: [...], removed: [...] }`.)

Most expensive, most consistent. Reach for this only when the other three don't fit.

## Recognising the pattern

Smells:

- The API response has a list field that "summarises what's active/open/pending" alongside the per-item data.
- Client code does `if (!snapshotSet.has(id)) treatAsClosed(id)` — see [positive-evidence.md](./positive-evidence.md).
- The bug is intermittent in a way that correlates with timing (slow connections, long-open tabs).
- The bug fixes itself on hard refresh — but only briefly, until new items arrive again.

## A subtler variant

Sometimes the snapshot is correct *but the order of events matters*. E.g. the snapshot is fetched via a long-running query that began at t=0; SSE delivers an event at t=2; the client processes the SSE event first (because the query is still running) then receives the snapshot at t=3 which silently overwrites the more-recent event-driven update.

Symptom: "I see the update flash on the screen, then it reverts."

Fix: include a server-issued sequence number (`as_of`) on the snapshot. The client ignores the snapshot if its `as_of` is older than the most recent event the client has processed.

## Case study

The AMP repo's "Bug E v3" was a textbook snapshot-race. The `/entries` API returned `open_streams: []` (computed at fetch time when no agent activity had happened). SSE later delivered entries with a `stream_id` that wasn't in the snapshot. The client classified the stream as closed because it wasn't in the cached snapshot. The bubble flipped to a green checkmark the moment the agent's first reasoning entry arrived — even though the stream was still open in the database.

Fix was Option 2 (invert to positive evidence): server returns `closed_streams: []` instead. Items not in the list are correctly left as "still open" pending an explicit close event.
