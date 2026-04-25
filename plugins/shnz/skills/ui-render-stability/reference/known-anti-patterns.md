# Known anti-patterns

Running list of generic render-instability anti-patterns this skill has caught. Each entry: one-line shape, link to the deep-dive reference file, brief case-study reference.

This file is the **self-improvement loop** for the skill. When a diagnostic surfaces a *generic* anti-pattern (one that could exist in another codebase), append a one-liner here. App-specific patterns belong in `.registry/<slug>.md`; codebase-specific findings belong in a repo-local skill.

## The list

| Shape (one-liner) | Deep dive | First seen |
|---|---|---|
| **Conditional layout chrome** — tab strip / header buttons / side panels rendered conditionally on data state; mount/unmount as data loads, producing visible layout shifts. | [conditional-chrome.md](./conditional-chrome.md) | AMP repo channel-creation flash, 2026-04-26 |
| **Empty / loading / no-data conflation** — single `if (!data) return null` for both initial-load and truly-empty states; the user sees `null → skeleton → empty illustration → real content` as separate transitions. | [skeleton-states.md](./skeleton-states.md) | AMP repo channel-creation flash, 2026-04-26 |
| **CLS from missing image / font dimensions** — `<img>` without width/height attributes; `font-display: swap` causing reflow when web fonts arrive. | [layout-shift.md](./layout-shift.md) | Generic (Web Vitals canon) |
| **Unstable context provider value** — `<Provider value={{...}}>` creates a fresh object every render; every consumer re-renders even when the field they read didn't change. | [cache-cascade.md](./cache-cascade.md) | Generic React anti-pattern |
| **Coarse cache key invalidation** — `invalidateQueries(['channel', id])` triggers re-fetch of every child slice; many components re-render simultaneously. | [cache-cascade.md](./cache-cascade.md) | Generic React Query anti-pattern |
| **Mount thrash from racing data sources** — two effects setting the same state from different sources, or `isReady` flag flipping false during background refetches. | [mount-thrash.md](./mount-thrash.md) | Generic React anti-pattern |

## Canonical fix primitives

When the same fix recurs across a codebase, codify it as a reusable component. The catalogue:

| Anti-pattern | Canonical fix primitive |
|---|---|
| Conditional layout chrome | [`<StableSlot>`](./stable-slot.md) — reserves layout space even when inner content is null. Drop in wherever you'd write `{cond && <SidebarOrPanel>}`. |

When you find a repeating fix shape during a diagnostic, write it up here so the next person reaches for the primitive instead of reinventing it.

## How to add an entry

When closing out a diagnostic:

1. Ask: was the root cause a **generic** pattern (could exist in another codebase) or **app-specific** (depends on this app's component structure)?
2. Generic → add a row here. App-specific → add to `.registry/<slug>.md`. Codebase-specific (file paths, exact selectors) → repo-local skill.
3. Keep the one-liner shape **diagnostic** (what to look for in frames or DevTools) not **postmortem** (what we did about it). The deep-dive holds the postmortem.
4. If the pattern is novel enough to need its own deep-dive file, create one in `reference/` and link from here.

## How to use this list

When opening a new diagnostic, scan this list first. If your before/after frames match one of the shapes, jump straight to the deep-dive — you may save 80% of the diagnostic time.

The entries are **shapes** to look for in frames or DevTools, not **causes** in code. The same shape can have multiple underlying code causes; the deep-dive walks through the common ones.
