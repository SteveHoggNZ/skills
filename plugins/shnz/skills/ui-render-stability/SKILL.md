---
name: ui-render-stability
kind: pattern
description: "Diagnose and fix visual instability in client-rendered UIs — flashing during navigation or state changes, layout shift (CLS), chrome elements that mount/unmount, content swaps without skeleton states, transition jank. Pattern skill: provides ffmpeg-based video frame analysis, the conditional-chrome anti-pattern catalogue, skeleton-state design rules, and a per-app registry of layout-chrome quirks. Trigger phrases include 'the UI flashes', 'screen flickers when', 'layout jumps', 'tabs appear and disappear', 'flashing during navigation', 'jumpy', 'janky transition', 'content snaps in'."
---

<!-- Claude Code adapter — the canonical procedure lives in core.md -->

This is a **pattern skill** (see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) in this marketplace). Read [core.md](./core.md) for the methodology, then load `reference/*.md` files on demand for the specific patterns you need.

## When to load this skill

The agent should pull this in whenever the bug class is "the UI is *visually unstable* during interactions or transitions" — flash, jump, jank, mount/unmount thrash. Concrete tells:

- The user says "flashes", "flickers", "jumps", "snaps in", "flashing", "janky".
- The user provides a video / screen recording showing visible discontinuity.
- The user reports "feels slow" but the network tab and React profiler look fine — perceived slowness is often visual instability, not actual latency.
- The user can't reproduce the bug in single screenshots — it only shows in motion.

This is **distinct from** [`ui-state-debugging`](../ui-state-debugging/), which is about *wrong state*. Render-stability is about *correct state, transitioned badly*.

## Claude Code specifics

- **Tool mapping**: `Bash` for ffmpeg frame extraction; `Read` to view extracted PNGs (Claude can analyse images directly); `Edit` for the fix; pair with [`agent-browser`](../agent-browser/) for live reproduction.
- **Pair with `ffmpeg`**: the unique technique here is video → frame analysis. Install once: `brew install ffmpeg` (macOS) or equivalent.
- **Pair with [`ui-state-debugging`](../ui-state-debugging/)**: when it's unclear whether the bug is wrong-state or unstable-render, run both methodologies. The state walk eliminates the wrong-state hypothesis quickly.

## At the start of every diagnostic

1. **Resolve the origin** of the app being debugged. Compute the slug per [reference/registry-format.md](./reference/registry-format.md).
2. **Load `.registry/<slug>.md`** if it exists — internalize the known conditional-chrome quirks for this app.
3. **If there's a video**, extract frames at the transition points using the ffmpeg recipe in [reference/video-frame-analysis.md](./reference/video-frame-analysis.md). Read each frame and characterise the layout delta.
4. **If there's no video**, ask the user to record one (`Cmd-Shift-5` on macOS), or use Playwright's video recording from a test rig (see [`ui-state-debugging/reference/test-rig-pattern.md`](../ui-state-debugging/reference/test-rig-pattern.md)).
5. Walk the anti-pattern catalogue in [core.md](./core.md) and identify which one(s) match.

## At the end of every diagnostic

- **App-specific learnings** (this app uses conditional chrome in component X; this app's skeleton state is missing for route Y) → update `.registry/<slug>.md`.
- **Generic anti-patterns** (a new class of render-instability worth catching elsewhere) → append to [reference/known-anti-patterns.md](./reference/known-anti-patterns.md).
- **Codebase-specific findings** (file paths, exact CSS selectors, framework-specific fix) → repo-local skill; see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md).
