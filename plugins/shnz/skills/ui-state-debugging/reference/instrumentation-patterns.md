# Instrumentation patterns

When React Devtools, console.log, and the network panel aren't enough — when you need to capture the *flow of state through the render loop* — these patterns let you instrument cheaply and dump from the console.

## The window-debug pattern

In the suspect component, push state observations to a window-scoped array on every render:

```tsx
function MyComponent({ id, status, isClosed }: Props) {
  // [DEBUG] capture every render with relevant state
  if (typeof window !== 'undefined' && id) {
    const w = window as any
    w.__myDebug = w.__myDebug ?? []
    if (w.__myDebug.length < 200) {  // cap to avoid runaway growth
      w.__myDebug.push({
        ts: Date.now(),
        id,
        status,
        isClosed,
      })
    }
  }
  // ... rest of component
}
```

Then in the browser console:

```js
// Filter for one entity
window.__myDebug.filter(d => d.id?.startsWith('019dc6'))
// or summarise
[...new Set(window.__myDebug.map(d => d.status))]
// or last N events
window.__myDebug.slice(-10)
```

## Why this beats `console.log`

- **Captures all renders, not just timed ones.** A render-loop bug fires hundreds of times; `console.log` floods the console while the array stays queryable.
- **Filterable post-hoc.** You don't have to know in advance which entity the bug is on. Push everything, filter when you spot the symptom.
- **Survives across React reconciliation.** The array lives on `window`, not in component state, so it persists through unmounts and re-mounts.
- **Captures multiple state sources.** You can push the props, the result of a context lookup, the value of a derived hook, and a computed flag — all in one record.

## Why not React Devtools

React Devtools is great for "what's the current state?" but bad for "what was the sequence of state changes that led here?". The Profiler tab can show timed renders but is heavy and doesn't preserve arbitrary state shape — you can only profile what's in props/state, not derived values.

## Variants

### Capture only on state change

If you want to see *transitions* rather than every render:

```tsx
const prevRef = useRef<typeof status | null>(null)
if (prevRef.current !== status) {
  w.__myDebug.push({ ts: Date.now(), id, from: prevRef.current, to: status })
  prevRef.current = status
}
```

### Capture cross-component flow

In two components on the same data path:

```tsx
// Component A
w.__flowDebug = w.__flowDebug ?? []
w.__flowDebug.push({ ts: Date.now(), at: 'A', state })

// Component B (downstream)
w.__flowDebug.push({ ts: Date.now(), at: 'B', state })
```

Sort by `ts` to see the actual order events propagated through the render tree.

### Capture context value identity

To detect "context provider re-rendered everyone unnecessarily":

```tsx
w.__ctxDebug = w.__ctxDebug ?? new Map()
w.__ctxDebug.set('lastValue', ctxValue)
// after several renders, check: are these the same reference?
console.log(w.__ctxDebug.get('lastValue') === w.__ctxDebug.get('previousValue'))
```

### Capture SSE / WebSocket events

In the SSE handler:

```tsx
function broadcastStreamStatus(event: StreamStatusEvent) {
  w.__sseEvents = w.__sseEvents ?? []
  w.__sseEvents.push({ ts: Date.now(), kind: 'stream_status', event })
  // ... existing handler
}
```

This is invaluable when the bug is "the client missed an SSE event" — you can verify post-hoc whether the event arrived at all.

## Removal hygiene

Instrumentation is **temporary**. Once the bug is found:

1. **Remove all `__myDebug` push lines** before committing.
2. **Don't leave `console.log` either** unless it's a high-value durable log (e.g. `[BUG-E SSE stream_status]`).
3. The lessons go in the failure-modes catalogue ([known-failure-modes.md](./known-failure-modes.md) for generic patterns; the repo-local skill for specifics).

If the instrumentation revealed a pattern worth catching in production (e.g. "this state transition should never happen but did"), turn it into a real `console.warn` with a clear `[ProjectName]` prefix or, better, an analytics event. Don't leave debug-style code in production.

## When to skip instrumentation

If you can reproduce the bug in a fresh isolated environment in under a minute (e.g. via a Playwright rig — see [test-rig-pattern.md](./test-rig-pattern.md)), you may not need to instrument. The rig captures the timeline structurally; instrumentation is for cases where the bug only happens in the user's environment under conditions you can't easily recreate.

## Vite HMR caveat

Vite's HMR doesn't always reload changes to React components cleanly when they participate in the context tree (see [hmr-context-providers.md](./hmr-context-providers.md)). If your instrumentation seems to not be firing, check that the served file actually contains your changes:

```bash
curl -s -H 'Sec-Fetch-Dest: script' -H 'Referer: http://localhost:port/' \
  'http://localhost:port/src/path/to/component.tsx' | grep '__myDebug'
```

If the served file lacks your changes, restart the dev server (kill the port, not just `restart`).
