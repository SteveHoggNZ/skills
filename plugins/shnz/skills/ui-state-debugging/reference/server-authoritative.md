# Server-authoritative state

When the server owns a lifecycle (a stream open/closed, a task pending/done, a connection live/closed), the client should **reflect** what the server says, not **infer** state from local heuristics.

## The trap

A common shape: the server has a real-time stream of events for a long-running operation. The client wants to show "is this still happening or done?" and reaches for a heuristic:

```js
// 15s of no events → must be done, hide the spinner
if (Date.now() - lastEventAt > 15_000) {
  showAsDone(streamId)
}
```

The intuition is "save a round-trip; the server doesn't need to send a redundant 'still going' event."

The intuition is wrong. The heuristic is doing the server's job, badly. Specifically:

- It can't tell the difference between "the agent is still working but quietly between actions" and "the agent crashed."
- Its threshold (15s? 60s? 5 min?) is a guess that will be wrong for some legitimate use case.
- When the heuristic fires and shows the wrong state, the user has no recourse — there's no event to correct it.

This is the **ghost-buster anti-pattern**: a heuristic that *looks* like it's protecting the user from stuck states but is actually creating wrong states whenever the heuristic's assumptions don't match reality.

## The principle

> The client renders what the server tells it. If the server hasn't told the client a state changed, the state hasn't changed (from the UI's point of view).

Three implications:

1. **The server must explicitly broadcast state changes.** "Stream closed" is an event, not an inference. If the server doesn't send the event, the client has no way to know.
2. **The server is responsible for cleanup of stale state.** A crashed worker that leaves a stream open is a *server* bug, not a client bug. The fix is a server-side sweep job that closes the stale row and broadcasts the close event.
3. **Unknown ≠ closed.** When the client doesn't have explicit "closed" evidence, render "still working" (a spinner). Don't infer closure from absence.

## How to retrofit

If you're inheriting code with a client-side heuristic of this shape:

### Step 1 — Remove the heuristic

Delete the timeout / activity-tracker. The bubble will now spin forever for crashed workers. **This is fine, temporarily.** It surfaces the real bug instead of papering over it.

### Step 2 — Add a server-side sweep

A periodic job (cron, or lazy-on-read) that finds stale lifecycle rows and closes them, broadcasting the close event:

```sql
UPDATE streams SET closed_at = NOW(), reason = 'timeout'
WHERE closed_at IS NULL AND last_activity_at < NOW() - INTERVAL '5 minutes'
RETURNING id;
-- then broadcast close events for each returned id
```

Lazy-on-read is the cheapest variant: in the read endpoint, also flag any "open but stale" rows as logically closed in the response. (The DB row stays open until the cron sweep — but the client sees the right thing.)

### Step 3 — Verify with a regression test

Test that an agent that goes idle without explicitly closing eventually shows as done in the UI, without the client having any timer logic.

## Recognising the trap

Smells:

- Client code with `setTimeout` / `setInterval` whose body is "if no events for N ms, mark X as done/stale/closed/error".
- Comments like `// safety net for crashed workers` or `// ghost-buster`.
- A magic-number timeout that's been tuned multiple times and still feels wrong.
- Bug reports clustering around "this only happens when the agent does Y for more than N seconds" — Y matches whatever your timeout was tuned for.

Fix shape: move the responsibility to the server. The client is a render layer.

## Pairs with

- [positive-evidence.md](./positive-evidence.md) — the related design pattern. A server that owns lifecycle should push positive-evidence events ("X is closed") not negative-evidence snapshots ("X is not in the open set").
