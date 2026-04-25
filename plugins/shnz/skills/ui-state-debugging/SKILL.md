---
name: ui-state-debugging
kind: pattern
description: "Diagnose state-discrepancy bugs in client-server apps — bubbles stuck spinning, indicators that won't clear, UI showing different data than the database, screenshots that don't match what other people see. Pattern skill (not a script): provides three-layer verification, instrumentation patterns, and design heuristics the agent composes from. Maintains a per-origin registry of debugging quirks for each app it has investigated. Trigger phrases include 'why is X still showing', 'the UI is stuck', 'looks wrong', 'state mismatch', 'screenshot disagrees with the database', 'works for me but not for them'."
---

<!-- Claude Code adapter — the canonical procedure lives in core.md -->

This is a **pattern skill** (see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) in this marketplace). Read [core.md](./core.md) for the full methodology, then load `reference/*.md` files on demand for the specific patterns you need.

## When to load this skill

The agent should pull this in whenever the bug class is "the UI/client is showing the wrong state." Concrete tells:

- The user says "stuck", "won't clear", "still spinning", "frozen", "looks wrong", "wrong status".
- The user has a screenshot that disagrees with what you can see live.
- The user retests after a fix and reports it's "still broken" — when in fact their browser cache/HMR may be stale.
- The user reports a behaviour you can't reproduce in your own session.

## Claude Code specifics

- **Tool mapping**: `Read` for reference files; `Bash` for the verification commands (DB queries, curl); `Write` for diagnostic instrumentation in source files.
- **Don't take the user's screenshot at face value.** Drive the test yourself before declaring the bug fixed. The skill emphasises this — see [reference/dont-trust-screenshots.md](./reference/dont-trust-screenshots.md).
- **Pair with a tool skill.** This skill provides methodology; pair with [`agent-browser`](../agent-browser/) (or your client's equivalent) to actually inspect the live UI.

## At the start of every diagnostic

1. **Resolve the origin** of the app being debugged (e.g. `http://localhost:4173`). Compute the slug per [reference/registry-format.md](./reference/registry-format.md).
2. **Load the per-app registry** if it exists: `.registry/<slug>.md`. Internalize the orientation, layer pointers, known false-positive bug shapes, and framework quirks before starting investigation. This is the skill's primary speed-up — a known false-positive shape can save the entire investigation.
3. Identify which **layer boundary** the bug crosses (DB↔API, API↔client, client cache↔render). See [reference/three-layer-verification.md](./reference/three-layer-verification.md).
4. Pick the cheapest layer to verify first — usually the DB.
5. Walk the layers in order. Stop where the data first goes wrong.

## At the end of every diagnostic

Two update channels — pick the right one for what you learned:

- **App-specific learnings** (a new false-positive shape on this app, a framework quirk that bit you): update `.registry/<slug>.md`. Bump `last_updated` and `visit_count`.
- **Generic anti-patterns** (the root cause was a shape that could exist in another codebase — "negative-evidence cache seed", "context provider HMR stall", "synthetic ID treated as real entity"): append a one-liner to [reference/known-failure-modes.md](./reference/known-failure-modes.md).

Codebase-specific findings (commands, file paths, project-specific bugs) belong in a **repo-local skill**, not here. The registry is for things that would still be true if the codebase were rewritten in a different language.
