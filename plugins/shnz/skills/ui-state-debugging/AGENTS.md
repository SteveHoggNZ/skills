# UI State Debugging (Codex adapter)

When the user describes a state-discrepancy bug ("UI is stuck", "still showing X after the fix", "wrong status", screenshot disagrees with what you see), follow the methodology in [core.md](./core.md).

## Codex specifics

- **Tool mapping**: `cat` / your editor for reference files; `bash` for the verification commands (DB, curl); your edit function for diagnostic instrumentation.
- **Pair with [`agent-browser`](../agent-browser/)** for the "verify what the client received" and "reproduce yourself" steps. This skill provides methodology; agent-browser provides the browser-driving recipe and per-site registry.

## At the start of every diagnostic

1. **Resolve the origin** of the app being debugged. Compute the slug per [reference/registry-format.md](./reference/registry-format.md).
2. **Load `.registry/<slug>.md`** if it exists — internalize the false-positive shapes and framework quirks before starting.
3. Identify which **layer boundary** the bug crosses (DB↔API, API↔client, client cache↔render). See [reference/three-layer-verification.md](./reference/three-layer-verification.md).
4. Pick the cheapest layer to verify first — usually the DB.
5. Walk the layers in order. Stop where the data first goes wrong.

## At the end of every diagnostic

- **App-specific learnings** → update `.registry/<slug>.md`.
- **Generic anti-patterns** → append a one-liner to [reference/known-failure-modes.md](./reference/known-failure-modes.md).
- **Codebase-specific findings** → repo-local skill; see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md).
