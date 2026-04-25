# UI Render Stability

A pattern catalogue for diagnosing and fixing visual instability in client-rendered UIs: flashing during navigation or state changes, layout shift (CLS), chrome elements that mount/unmount, content swaps without skeleton states, transition jank.

## Why this skill exists

Render-stability bugs are visible in motion but invisible in screenshots. They feel like "the app is slow" or "feels janky" — perceptions that are hard to triage from a single still frame. The fix patterns are well-known (always-on chrome, skeleton states, persistent layout containers) but the *diagnosis* requires looking at the UI in motion and characterising what changed when.

This is a **pattern catalogue, not a script** (see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md)). The agent picks the relevant patterns based on what the video shows.

## The methodology in one sentence

> Extract frames at transition boundaries, characterise what mounted/unmounted/shifted in each step, then map each to its anti-pattern and fix.

## Per-app registry (read first)

Before any frame extraction, identify the origin of the app and load its registry entry:

```
1. Resolve origin: scheme://host:port (e.g. http://localhost:4173)
2. Compute slug: lowercase, replace `.`/`:` with `-`, drop default ports
3. Read .registry/<slug>.md if it exists
```

The registry captures **app-specific conditional-chrome quirks** — components that previous diagnostic sessions found to mount/unmount, conditional-render patterns the app overuses, parts of the codebase known to be CLS-heavy. A familiar app's quirks are 80% of the diagnostic.

Format: [reference/registry-format.md](./reference/registry-format.md).

## Procedure (composable, not linear)

### Step A — Get the motion artifact

If you don't have a video yet:

- **User-recorded**: `Cmd-Shift-5` on macOS (5-second clips are usually enough for a single transition).
- **Agent-recorded**: Playwright with `recordVideo` — see [`ui-state-debugging/reference/test-rig-pattern.md`](../ui-state-debugging/reference/test-rig-pattern.md). The output `.webm` works directly with ffmpeg.
- **Live observation**: Chrome DevTools → Rendering tab → enable "Paint flashing" + "Layout shift regions". Reproduce the interaction. The painted boxes show what re-rendered; the shift overlay highlights CLS.

### Step B — Extract frames at scene changes

Don't extract every frame (overkill); extract at transitions. ffmpeg's scene detection finds them automatically:

```bash
ffmpeg -i input.mp4 -vf "select='gt(scene,0.03)',showinfo" -vsync vfr -f null - 2>&1 \
  | grep "showinfo.*pts_time" | awk -F'pts_time:' '{print $2}' | awk '{print $1}'
```

The `0.03` threshold catches subtle layout shifts; raise to `0.10` for only major scene changes. Output: a list of timestamps where significant pixel change occurred. These are your candidate flash points.

Then extract one frame just before and one frame just after each scene change:

```bash
for t in $TIMESTAMPS; do
  before=$(echo "$t - 0.05" | bc)
  ffmpeg -ss $before -i input.mp4 -frames:v 1 -q:v 2 frame_${t}_before.png -loglevel error
  ffmpeg -ss $t      -i input.mp4 -frames:v 1 -q:v 2 frame_${t}_after.png  -loglevel error
done
```

Full recipe: [reference/video-frame-analysis.md](./reference/video-frame-analysis.md).

### Step C — Characterise each transition

For each (before, after) pair, identify what changed. The categories:

- **Layout chrome appeared/disappeared** — tabs, headers, side panels mounted or unmounted. The chrome wasn't there in one frame and was in the next (or vice versa). → see [reference/conditional-chrome.md](./reference/conditional-chrome.md).
- **Content swapped without intermediate state** — main pane went from rich content directly to empty (or vice versa) with no skeleton. → see [reference/skeleton-states.md](./reference/skeleton-states.md).
- **Element shifted position** — a component is in both frames but at a different y-coordinate, pushing siblings around. CLS. → see [reference/layout-shift.md](./reference/layout-shift.md).
- **Cache invalidation cascade** — many elements re-rendered simultaneously even though only one source of truth changed. → see [reference/cache-cascade.md](./reference/cache-cascade.md).
- **Mount/unmount thrash** — the same component flickered between visible and invisible across multiple frames within a single transition. → see [reference/mount-thrash.md](./reference/mount-thrash.md).

A single flash usually maps to one or two categories. Multiple flashes in one interaction (like the AMP channel-creation case) usually involve all of these in sequence.

### Step D — Map to fix

Each category has a canonical fix. Read the relevant reference file. The general principle:

> **Layout should be persistent. Content should be progressive.**

Persistent layout = the chrome (header, tabs, sidebar, panels) is always rendered, even when its data isn't loaded. Use disabled / placeholder / "0 items" states; don't conditionally mount the wrapper. Codify the wrapper as a `<StableSlot>` primitive (see [reference/stable-slot.md](./reference/stable-slot.md)) once you've applied the fix more than once — it makes intent explicit and stops the inline `min-width` trick from drifting.

Progressive content = the main pane fills in via skeleton → low-fidelity preview → final content, instead of empty → snap-to-final.

### Step E — Verify the fix

Re-record the video, re-run scene detection, count the transitions. A successful fix reduces the number of detected scene changes (and the perceived flash count). The frames at those transitions should now show only content change, not layout chrome change.

If you can't reduce to zero scene changes, document the residual ones in the app registry (some are unavoidable — e.g. a route change to a fundamentally different layout).

### Step F — Update the registries

- **App-specific learnings** (this app's component X is known to mount conditionally; this app uses pattern Y for skeleton states) → `.registry/<slug>.md`.
- **Generic anti-patterns** (a new class of render-instability worth catching) → [reference/known-anti-patterns.md](./reference/known-anti-patterns.md).
- **Codebase-specific findings** (exact files, exact selectors, framework-specific fixes) → repo-local skill.

## Tools the skill assumes

- `ffmpeg` and `ffprobe` (frame extraction, metadata).
- A browser with DevTools (Chrome / Edge for the Rendering tab, Firefox for layout-shift devtools).
- Optional: [`agent-browser`](../agent-browser/) for driving the reproduction; Playwright for recording.

## Pairs with

- [`ui-state-debugging`](../ui-state-debugging/) — when it's unclear whether the bug is wrong-state or unstable-render. Often both skills get loaded together; the state walk eliminates the wrong-state hypothesis quickly, leaving render-stability as the actual cause.
- [`agent-browser`](../agent-browser/) — for live reproduction with the per-site login/navigation knowledge.

## Anti-patterns this skill is *against*

- **Adding `transition: opacity 200ms`** to mask the flash. That hides the symptom, not the cause; the layout shift is still happening, just smoothly. Real fix: don't shift in the first place.
- **`will-change: transform`** sprayed on every component "for performance". It allocates GPU layers per element; usually makes things worse. Use only after profiling.
- **Wrapping everything in `Suspense`** as a default. Suspense boundaries with no skeleton fall back to nothing → invisible flash. Either the boundary has a skeleton, or it shouldn't be a boundary.

## See also

- [reference/video-frame-analysis.md](./reference/video-frame-analysis.md) — ffmpeg recipes
- [reference/conditional-chrome.md](./reference/conditional-chrome.md) — the most common cause
- [reference/skeleton-states.md](./reference/skeleton-states.md) — design rules for "loading" vs "empty" vs "no data"
- [reference/known-anti-patterns.md](./reference/known-anti-patterns.md) — running list
- [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) — how this skill fits with `ui-state-debugging` and `agent-browser`
