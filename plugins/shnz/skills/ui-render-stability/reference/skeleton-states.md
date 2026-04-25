# Skeleton states (loading vs empty vs no-data)

Three distinct UI states get conflated as "the empty state", and using the wrong one is a major source of perceived flash. Each has a clear definition and a clear visual treatment.

## The three states

| State | Meaning | Visual |
|---|---|---|
| **Loading** | The data is currently being fetched. Content will arrive. | Skeleton placeholder with the *shape* of the eventual content. Pulsing or shimmering. |
| **Empty** | The data fetched successfully and is empty. There is no content to show, and there might never be (e.g. a new account, an empty inbox). | Illustrative empty-state with a CTA ("Create your first…"). |
| **No data yet** | The data is not loadable in this context (the user hasn't done X yet). Subtly different from "empty". | Inline hint or disabled placeholder; not a full-screen empty illustration. |

## Why conflating them flashes

Imagine `<MainPane>` with this logic:

```tsx
function MainPane({ data }) {
  if (!data) return null  // ← worst: invisible during load
  if (data.length === 0) return <EmptyIllustration />
  return <ContentList items={data} />
}
```

The user navigates to a new view. For ~200ms, `data` is undefined → `MainPane` renders nothing (a white space the size of nothing). Then `data` arrives as `[]` → `EmptyIllustration` mounts, taking up some space. Then user creates an item → `data` is `[{…}]` → swap to `ContentList`, taking up different space.

That's three layout transitions for one user action. The first two are flashes; the third may also be.

Fix:

```tsx
function MainPane({ data, isLoading }) {
  if (isLoading) return <ContentSkeleton />            // size = ContentList
  if (data.length === 0) return <EmptyState />          // size = ContentList (with empty illustration filling the same slot)
  return <ContentList items={data} />
}
```

All three states occupy the same vertical space. The transition between them is content-only; no layout shift.

## Skeleton design rules

A skeleton is **not** "vague gray rectangles." It's a low-fidelity preview of the final layout:

- **Same dimensions** as the eventual content. If a list shows 10 rows of 60px each, the skeleton shows 10 rows of 60px each.
- **Same vertical rhythm** — same gaps, same group dividers. The eye should land in the same place when content swaps in.
- **Subtle animation** (pulse / shimmer) to communicate "this is loading", not "this is broken." But don't overdo it — too much animation distracts.
- **Not styled like real content** — desaturated, lighter weight. The user should never confuse the skeleton for real but mis-formatted data.

## When to skip the skeleton

If the data loads in <100ms (warm cache, local state), the skeleton flashes for a single frame and looks worse than no skeleton. Threshold: only show the skeleton if loading takes more than ~150ms. In React Query / SWR, you can use `isFetching` plus a delay:

```tsx
const showSkeleton = useDelayedTrue(isFetching, 150)
```

Otherwise the optimistic-render pattern (show stale data while fetching fresh) is better — the user sees something correct that updates, instead of skeleton → real.

## Empty states are different from "no data yet"

Distinguish:

- **First-time empty** — "You don't have any channels yet. [Create channel]" — a friendly empty illustration with a CTA.
- **Filtered-to-empty** — "No channels match 'foo'. Clear filters?" — minimal hint, easy to undo.
- **No data in this scope** — "Pick an item to see details" — small inline hint, not a full-screen illustration.

Each warrants different visual treatment but all should occupy the same layout slot as the "has data" state. The user shouldn't see the page rearrange just because a filter changed.

## The "snap" before content arrives

A common pattern: render `null` while loading, then snap-mount the real content. Even with very fast data, the snap is perceptible at high frame rates.

Fix: always render the content's outer container (with skeleton inside). The container stays put; only the inside swaps. This is the **persistent layout** principle from [conditional-chrome.md](./conditional-chrome.md) applied to single components.

## Pairs with

- [conditional-chrome.md](./conditional-chrome.md) — the same principle applied at the layout-chrome level.
- [layout-shift.md](./layout-shift.md) — when skeleton dimensions don't match real content dimensions.
