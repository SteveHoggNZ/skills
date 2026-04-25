# Mount/unmount thrash

The same component flickers between visible and invisible across multiple frames within a single transition. Worst case of [conditional-chrome.md](./conditional-chrome.md): not just "the chrome appeared once when it shouldn't" but "the chrome appeared, disappeared, appeared again."

## What it looks like

In dense frame extraction (every 50ms or so) around a transition, you see a component:

- **Frame N**: present
- **Frame N+1**: absent
- **Frame N+2**: present
- **Frame N+3**: absent (or final state)

That's two unmount events for one user action. Each unmount destroys the component's internal state (focus, scroll position, in-flight animations) and the re-mount has to rebuild it from scratch.

## Common causes

### Race between data sources

```tsx
// ❌ Two effects setting the same state can thrash
useEffect(() => { setData(fastSource) }, [fastSource])
useEffect(() => { setData(slowSource) }, [slowSource])
```

`fastSource` arrives → `setData(real)` → component renders. Then `slowSource` arrives 50ms later with `null` → `setData(null)` → component unmounts. Then `slowSource` resolves → `setData(real)` → component re-mounts.

Fix: pick one source of truth. If you need to merge, do it in a `useMemo`, not via competing effects.

### Boolean prop derived from changing values

```tsx
// ❌ `isReady` flickers as data loads
const isReady = !!data && !isLoading && !isError && !isFetching
return isReady ? <Content /> : null
```

If `isFetching` flips on background refetches, `isReady` flips, `Content` mounts/unmounts. Fix: don't gate mounting on `isFetching` — show stale data while fetching (`isLoading` is enough for first-time gating).

### Suspense boundary toggling

A `<Suspense>` boundary swaps between `fallback` and `children` when any child reads from a suspending data source. If multiple sources suspend in sequence (one resolves, another suspends), the boundary toggles back to fallback.

Fix: hoist suspending reads to a single coordinated `<Suspense>` parent, or use `startTransition` to batch updates.

### Transition-from-undefined

```tsx
// ❌ undefined → empty array → array of items → 3 mount events
const items = data?.items
return <ItemList items={items} />  // ItemList unmounts when items is undefined
```

Inside `ItemList`, conditional rendering on `items.length` means the component renders nothing on first pass (`items` is undefined), then renders empty state, then renders content. Each is a separate React commit; the component's internal effects re-run.

Fix: default the prop. `items={items ?? []}`. Render empty state for length 0; never render `null`.

## Diagnosing

The video usually shows mount thrash as a "flicker" that looks like a single longer flash, but is actually multiple short ones. Use a denser frame extraction (every 16-33ms) around the suspected transition:

```bash
ffmpeg -i input.mp4 -vf "fps=60" /tmp/frames/f_%04d.png
```

Walk through the frames in sequence. You'll see the component flickering across N frames where N > 1.

In React DevTools Profiler, look for multiple consecutive commits touching the same component path within a single user action. Each commit that mounted-then-unmounted (or vice versa) is one thrash.

## The fix principle

Components should mount once per logical existence. If a component represents "the user's profile panel", it mounts when the panel is opened and unmounts when it's closed — not whenever any of its inputs flicker.

Apply by working backward from the unmount: what flipped the prop/state that caused the unmount? Was that flip *meaningful* (the user closed the panel) or *incidental* (a refetch made `isReady` momentarily false)? Eliminate incidental causes.

## Pairs with

- [conditional-chrome.md](./conditional-chrome.md) — the simpler form of the same problem (one mount/unmount instead of multiple).
- [cache-cascade.md](./cache-cascade.md) — when the trigger for the thrash is a cascade of cache invalidations.
