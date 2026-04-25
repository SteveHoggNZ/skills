# Known failure modes

Running list of generic UI state-discrepancy anti-patterns this skill has caught. Each entry: one-line shape, link to the deep-dive reference file, brief case-study reference.

This file is the **self-improvement loop** for the skill (see SKILL.md). When a diagnostic surfaces a *generic* anti-pattern (one that could exist in another codebase), append a one-liner here. Codebase-specific findings belong in a repo-local skill, not here.

## The list

| Shape (one-liner) | Deep dive | First seen |
|---|---|---|
| **Negative-evidence cache seed** — API returns `open_X: []` snapshot; client treats absence as closure; new items arriving via SSE after the snapshot are silently mis-classified as closed. | [positive-evidence.md](./positive-evidence.md) | AMP repo, "Bug E v3", 2026-04-25 |
| **Client-side ghost-buster** — heuristic that hides UI indicators after N seconds of no activity; can't distinguish "agent quiet between steps" from "agent crashed"; fires during legitimate long-running operations. | [server-authoritative.md](./server-authoritative.md) | AMP repo, "Bug E v2 (UI ghost-buster)", 2026-04-25 |
| **Synthetic ID treated as real entity** — UUID derived from inputs (no DB row) gets the same UI treatment as a real entity; lifecycle indicators on it never resolve. | [synthetic-vs-real-entities.md](./synthetic-vs-real-entities.md) | AMP repo, atomic /messages stream_ids, 2026-04-25 |
| **HMR can't replace context providers** — Vite reports module replaced; React tree never re-mounts the provider; consumers continue subscribing to stale value; user sees old behaviour after "reload". | [hmr-context-providers.md](./hmr-context-providers.md) | AMP repo, EntriesStreamContext refactor, 2026-04-25 |
| **Snapshot race** — API response embeds a snapshot field alongside per-item data; SSE updates the items but not the snapshot; client decisions based on the snapshot are wrong for new items. | [cache-snapshot-races.md](./cache-snapshot-races.md) | AMP repo, "Bug E v3", 2026-04-25 |
| **Trusting the user's screenshot** — declaring fixed/broken based on the user's report without reproducing in a fresh session; user's stale bundle is the most common cause of false reports either way. | [dont-trust-screenshots.md](./dont-trust-screenshots.md) | AMP repo, multiple "still broken" iterations, 2026-04-25 |

## How to add an entry

When closing out a diagnostic:

1. Ask: was the root cause a **generic** pattern (could exist in another codebase) or **codebase-specific** (depends on this project's architecture)?
2. Generic → add a row here. Codebase-specific → add to a repo-local skill, not here.
3. Keep the one-liner shape **diagnostic** (what to look for) not **postmortem** (what we did about it). The deep-dive file holds the postmortem.
4. Bump the case-study reference if a new project hits the same shape — accumulating "first seen / also seen in" data is useful evidence that the pattern is real and worth catching.
5. If the pattern is novel enough to need its own deep-dive file, create one in `reference/` and link from here.

## How to use this list

When opening a new diagnostic, scan this list first. If the user's symptom matches one of the shapes (e.g. "indicators won't clear", "wrong status after fix"), jump straight to the deep-dive — you may save 90% of the diagnostic time.

The entries are deliberately phrased as **shapes**, not **causes** — the same shape can have multiple underlying causes in different codebases. The deep-dive file walks through the causes that have been seen.
