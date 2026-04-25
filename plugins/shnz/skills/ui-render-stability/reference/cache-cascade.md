# Cache invalidation cascades

Many components re-render simultaneously even though only one source of truth changed. Visible as a wave of repaints across the screen during state transitions.

## What it looks like

In Chrome DevTools → Rendering → Paint flashing enabled, reproduce the interaction. You'll see the entire screen flash green/orange briefly. In React DevTools Profiler, a single user action shows N component re-renders where N is the entire tree.

The flash you see in the video is the visible side of this — many components re-mounting or re-laying-out at once because the cache decided "everything is stale."

## Common causes

### Coarse-grained cache keys

In React Query / SWR / Apollo:

```ts
// ❌ Invalidating the whole channel cascades to every consumer
queryClient.invalidateQueries({ queryKey: ['channel', channelId] })

// ✅ Invalidate only the slice that changed
queryClient.invalidateQueries({ queryKey: ['channel', channelId, 'messages'] })
```

If many slices are children of one cache key, invalidating the parent re-fetches them all → all subscribers re-render → wave of paints.

### Context provider value identity changes

```tsx
// ❌ Every render creates a new value object → every consumer re-renders
<MyContext.Provider value={{ data, setData }}>

// ✅ Memo the value
const ctxValue = useMemo(() => ({ data, setData }), [data, setData])
<MyContext.Provider value={ctxValue}>
```

When the provider's `value` prop is a fresh object every render, every consumer re-renders, even ones that don't read the changed field.

### Subscribing to too much

```tsx
// ❌ Subscribes to the entire channel; re-renders on any change
const channel = useChannel(channelId)

// ✅ Subscribes only to what you need; re-renders only when name changes
const channelName = useChannel(channelId, ch => ch.name)
```

Selector hooks (Zustand, Redux toolkit, Jotai) let consumers subscribe to slices. Selecting too broadly means re-rendering on unrelated changes.

### React Context for high-frequency state

Context propagates by re-rendering all consumers. For state that updates on every keystroke or every animation frame, use a different mechanism:

- A `useSyncExternalStore` selector hook
- A separate state library (Zustand, Jotai, Valtio) that supports fine-grained subscriptions
- Refs + manual updates for cases where you don't need React rendering at all

## Diagnosing

Open React DevTools → Profiler → record the interaction. Look for:

- A single commit that touched dozens of components → cascade.
- The same component re-rendered many times in one commit → its parent's value/props are unstable.

Cross-reference with the video frames. A flash at t=3.01 + a profiler commit at t=3.01 covering 50+ components = cache cascade.

## The fix shape

Two complementary strategies:

1. **Narrow the cache keys**. Make invalidation precise. The cost is more bookkeeping; the benefit is targeted re-renders.
2. **Memoize provider values and props**. Stop unstable identities from triggering re-renders that wouldn't otherwise happen. The cost is `useMemo` boilerplate; the benefit is correct propagation.

Both are usually needed. Start with the cache, then memoize what's still over-rendering.

## When the cascade is unavoidable

Some operations legitimately invalidate a lot of state (logout, workspace switch, account switch). For those, accept the wave but make it *visually one transition* — wrap the affected region in `<Suspense>` with a skeleton, so the user sees one explicit "loading" state rather than 50 component flashes.

## Pairs with

- [mount-thrash.md](./mount-thrash.md) — when the cascade includes unmounts and re-mounts (worst case).
- [conditional-chrome.md](./conditional-chrome.md) — when the cascade triggers chrome that shows/hides.
