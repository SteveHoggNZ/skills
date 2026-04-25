---
name: inspect-session
kind: procedure
description: "Parse a session JSONL transcript and report metrics: start/end time, wall-clock duration, input/output/cache tokens, cache hit rate, user/assistant turn counts, tool-call breakdown, slash commands, assistant-turn latency (min/median/p90/max), total USD cost with per-bucket breakdown, and cost per user turn. Use when the user says 'inspect this session', 'session metrics', 'how much did this cost', 'how many tokens', 'profile this session', or invokes /inspect-session. Outputs markdown by default; --json for machine-readable. Invocation is **runtime-dependent**: GitHub Copilot CLI collects metrics automatically on session end via hook; Claude Code requires manual invocation."
argument-hint: "[session-id | path/to/session.jsonl] [--json]"
---

<!-- Runtime-agnostic skill adapter — canonical procedure in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Runtime modes

This skill works in both GitHub Copilot CLI and Claude Code, but invocation differs:

| Runtime | Mode | When metrics are collected |
|---------|------|---------------------------|
| **GitHub Copilot CLI** | Automatic | On session end (via `onSessionEnd` hook) |
| **Claude Code** | Manual | User invokes `/inspect-session` or natural-language trigger |

Both generate identical metrics; only the timing and trigger differ. See [reference/copilot-hook.md](./reference/copilot-hook.md) for the Copilot integration pattern.

## Implementation (both runtimes)

- **Metric computation**: The bundled `metrics.py` script (stdlib-only, zero deps) parses JSONL and emits metrics.
- **Argument parsing** (Claude Code only): Accept optional session UUID, absolute path, or nothing (defaults to most recent in project). Trailing `--json` flag switches output.
- **Output**: Markdown (terminal-friendly) by default; JSON for pipes.
- **Session file location**: JSONL transcripts live in `~/.claude/projects/<project>/` (Claude Code) or wherever Copilot stores sessions.

## Typical first interaction (Claude Code)

1. User says "inspect this session" or `/inspect-session`.
2. Run `python3 <skill-dir>/metrics.py` with no args → report on the current project's most recent session.
3. Present the markdown output. Flag any `[unavailable]` fields (e.g. cost when the model isn't in the price table) so the user knows the gap.
4. If the user asks about a different session, re-run with `--session-id` or a path.

## Reference files

- [reference/pricing.md](./reference/pricing.md) — how to update the embedded price table when Anthropic ships new models or adjusts rates.
- [reference/copilot-hook.md](./reference/copilot-hook.md) — inspect-session hook implementation detail (TypeScript + Python examples, `.metrics.json` format, aggregation). Plugin-level hook contract: [hooks/on_session_end.md](../../../hooks/on_session_end.md).
