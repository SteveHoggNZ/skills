# StableSlot — the canonical fix for conditional layout chrome

The recurring fix for the [`conditional-chrome.md`](./conditional-chrome.md) anti-pattern is a tiny wrapper component that reserves layout space even when its inner content is null. Codify it as a primitive in your project — call it `<StableSlot>` (or whatever name fits your codebase) — and reach for it every time you'd otherwise write `{cond && <PanelOrSidebar>}`.

## The shape

```tsx
import type { CSSProperties, ReactNode } from 'react'

export interface StableSlotProps {
  /** Whether this slot should occupy any space at all. When false, returns
   *  null. When true, the outer wrapper renders with reserved dimensions
   *  even if `children` is empty. */
  visible?: boolean
  /** Reserved minimum width — pass for sidebars / side panels in a flex row. */
  minWidth?: string | number
  /** Reserved minimum height — pass for slots in a flex column. */
  minHeight?: string | number
  /** Outer wrapper className. Default: `'flex h-full shrink-0'` (sidebar shape). */
  className?: string
  children: ReactNode
}

export function StableSlot({ visible = true, minWidth, minHeight, className = 'flex h-full shrink-0', children }: StableSlotProps) {
  if (!visible) return null
  const style: CSSProperties = {}
  if (minWidth !== undefined) style.minWidth = typeof minWidth === 'number' ? `${minWidth}px` : minWidth
  if (minHeight !== undefined) style.minHeight = typeof minHeight === 'number' ? `${minHeight}px` : minHeight
  return <div className={className} style={style}>{children}</div>
}
```

## The two gates — get this right or it doesn't work

The component takes **two gates** that mean different things:

| Gate | Meaning | Effect |
|---|---|---|
| `visible` (outer prop) | "should this slot exist at all?" — explicit user intent (panel collapsed, sidecar closed) | When false, returns `null`. The slot truly disappears. |
| Inner `{data && <Panel data={data} />}` | "is the slot's *content* loaded?" | When data is null, slot stays mounted with reserved space; only the inner content is empty. |

Get this right or you've reproduced the original bug:

```tsx
// ❌ Wrong — selectedChannel collapses the slot during transitions
<StableSlot visible={inspectorVisible && !!selectedChannel} minWidth="320px">
  <InspectorPanel data={selectedChannel} />
</StableSlot>

// ✅ Right — visible is for explicit hide/show, inner gate is for data
<StableSlot visible={inspectorVisible} minWidth="320px">
  {selectedChannel && <InspectorPanel data={selectedChannel} />}
</StableSlot>
```

The first form repeats the original bug because the OUTER gate now flips on data state. The second form keeps the slot stable across data transitions.

## When to use

Apply whenever you'd otherwise write:

```tsx
{userIntent && dataLoaded && (
  <div className="flex h-full shrink-0">  {/* layout chrome */}
    <Panel data={dataLoaded} />
  </div>
)}
```

Three conditions for the rewrite:
1. The wrapper div is layout chrome (sidebar, sidecar, panel, header) — not just a styling div around inline content.
2. The data condition (`dataLoaded`) can flip during legitimate transitions (channel switch, route change, refetch).
3. The slot's footprint is meaningful (>50px in the dimension that would collapse).

If any condition is missed, the wrapper isn't worth it; use the plain conditional.

## When NOT to use

- The wrapper truly should disappear when its content is gone (e.g. an empty card grid that should leave no trace). Use plain conditional rendering.
- The "data loaded" condition only flips on initial page load and never again (e.g. the user's profile data). Skeleton-state pattern is better here ([`skeleton-states.md`](./skeleton-states.md)).
- The slot's footprint is small enough that the layout shift is imperceptible (<20px or so). Don't add ceremony for nothing.

## Pairs with skeleton states

`StableSlot` reserves the **footprint**. A skeleton component fills the **content** while data loads. Use both together:

```tsx
<StableSlot visible={inspectorVisible} minWidth={320}>
  {selectedChannel ? (
    <InspectorPanel data={selectedChannel} />
  ) : (
    <InspectorSkeleton />
  )}
</StableSlot>
```

The slot keeps the right-rail width stable; the skeleton tells the user "loading, not empty"; the real panel swaps in without any layout shift. Three coordinated patterns producing one smooth transition.

## Generalisation: the same shape for vertical slots

The default className `flex h-full shrink-0` is for horizontal sidebars. For vertical slots (header, footer, status bar):

```tsx
<StableSlot visible={hasNotifications} minHeight={48} className="flex w-full shrink-0">
  {notifications && <NotificationBar items={notifications} />}
</StableSlot>
```

Pass the right `className` for the parent flex direction; pass `minHeight` instead of `minWidth`.

## Implementation in this codebase

If you're working in the AMP repo, the primitive lives at:

```
apps/ui/src/components/layout/StableSlot.tsx
```

Search for existing usages with `import { StableSlot }` to see the canonical applications and the comment pattern around them.

## Anti-patterns this primitive replaces

- Inline `style={{ minWidth: '320px' }}` on an outer div with the gating moved inside — works, but every site reinvents the wheel and the next dev removes the inline style without realising it was load-bearing.
- Empty placeholder components rendered "just to keep the layout" — `<div className="..." />` with no semantics. The `StableSlot` primitive makes the intent ("this is a reserved layout slot") explicit.
- Conditional rendering with subsequent CSS gymnastics to mask the layout shift (transition: width, transform: translateX, etc.). Those mask the symptom; the slot prevents the cause.
