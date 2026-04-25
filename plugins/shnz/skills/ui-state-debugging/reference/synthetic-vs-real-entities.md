# Synthetic vs real entities

When the system uses both *real* IDs (rows in a database table) and *synthetic* IDs (deterministic UUIDs derived from inputs, hashes, namespacing), the UI must distinguish them or you'll get indicators that never resolve.

## What a synthetic ID looks like

Common shapes:

- **Deterministic UUID**: `uuid_v5(namespace, "agent_id:channel_id")` — derives a stable ID from inputs without ever creating a row.
- **Hash-derived**: `sha256(messageBody).slice(0,32)` — used for grouping or correlation.
- **Composite key flattened**: `${parentId}:${childKey}` — derived for convenience but never persisted.
- **Atomic-message stream_id**: a stream_id is generated for narrative grouping when an agent posts a one-shot message that *doesn't* go through the streams API. There's no `streams` row for it.

## The trap

Code that handles "is this entity in state X?" by querying a real table will return "no row" for synthetic IDs. If the UI then interprets "no row" as "still loading", the indicator spins forever:

```js
const status = await db.query('SELECT status FROM streams WHERE id = ?', syntheticId)
//             returns null
if (status === null) {
  showSpinner() // ← wrong: never resolves
}
```

The UI is asking the wrong question. The right question is "does this entity *exist* in the lifecycle table?" — if no, then it's not a tracked lifecycle, it's a one-shot, and should render as completed.

## The fix

In responses that include status for IDs, classify each ID into three buckets:

1. **Real + open** — exists in the lifecycle table, not yet closed. Render as "in progress".
2. **Real + closed** — exists, has been closed. Render as "done".
3. **Synthetic / phantom** — does not exist in the lifecycle table at all. Render as "done" (it was a one-shot).

The wrong classification is binary: "exists and open" vs "everything else". That treats synthetic IDs as if they're closed real IDs, which is *correct in this case* but for the wrong reason — and the moment a slow database write makes a real ID *temporarily* look like a synthetic one (the row hasn't landed yet but the SSE event has), you get wrong-state.

The right classification is ternary, and the synthetic case is identified by `LEFT JOIN ... WHERE table.id IS NULL`:

```sql
SELECT
  in_id.id,
  table.id IS NOT NULL AS exists,
  table.closed_at IS NULL AS is_open
FROM unnest($1::uuid[]) AS in_id(id)
LEFT JOIN lifecycle_table table ON table.id = in_id.id
```

Then in the response: `synthetic` (=closed) gets the same UI treatment as `real + closed` but for the right reason.

## The principle

> Distinguish "this entity has no lifecycle" from "this entity's lifecycle is unfinished". Conflating them produces indicators that never resolve.

## Recognising the pattern

Smells:

- Indicators that spin forever on certain message types but not others.
- The UI works fine for messages from one code path but hangs for another.
- You find a `null` check that handles the case as if it's a "not yet loaded" state.
- Database query for status returns no row for IDs that show up in the UI.

## Avoiding the bug at design time

Two options:

1. **Don't use synthetic IDs in fields the UI reads as lifecycle indicators.** If you need to group items, use a separate `group_id` field rather than reusing `stream_id`.
2. **Always materialise a lifecycle row for synthetic IDs.** A one-shot message gets a row that's `INSERT … with closed_at=NOW()` on creation. Then the UI never sees a missing row.

The second is generally cleaner — you preserve the invariant "every ID the UI sees has a lifecycle row" and the cost is one extra row per atomic message.

## Case study

In the AMP repo, atomic `/messages` sends generated a deterministic stream_id (UUIDv5) for narrative grouping but never created a row in `message_streams`. The UI's seed logic correctly classified these as closed (because the stream wasn't in the open set), but only by accident — the same code path *also* incorrectly classified real-but-recently-arrived streams as closed. Fixing the negative-evidence bug ([positive-evidence.md](./positive-evidence.md)) required explicitly handling the synthetic case in the server's `closed_streams` query, otherwise atomic messages started spinning forever.
