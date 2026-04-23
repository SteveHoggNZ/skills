---
name: inspect-session
description: "Inspect a Claude Code session JSONL transcript and report metrics: start/end time, wall-clock duration, input/output/cache tokens, cache hit rate, user and assistant turn counts, tool-call breakdown, slash-command usage, assistant-turn latency (min/median/p90/max), total USD cost with per-bucket breakdown, and cost per user turn. Use when the user says 'inspect this session', 'session metrics', 'how much did this conversation cost', 'how many tokens did I use', 'profile my session', or invokes /inspect-session. Reads JSONL files from ~/.claude/projects/<project>/; defaults to the most recent session in the current project. Outputs markdown by default; --json for machine-readable."
argument-hint: "[session-id | path/to/session.jsonl] [--json]"
---

<!-- Claude Code adapter — canonical procedure in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Claude Code specifics

- **Parse `ARGUMENTS`**: accept an optional session UUID, an absolute path to a `.jsonl`, or nothing (defaults to the most recent session in the current project). A trailing `--json` flag switches output to machine-readable JSON.
- **Run the bundled script with `Bash`**: `python3 <skill-dir>/metrics.py [args]`. The script is stdlib-only (no `pip install`, no runtime deps).
- **Do not re-implement the parser in Claude's head.** The deterministic script is faster, cheaper, and gives the same answer every time. Only fall back to hand-parsing the JSONL if the user asks a *custom* question the script doesn't cover ("which tool produced the most tokens of output?"), and say so explicitly.
- **Show the output verbatim** (or near-verbatim) by default. The markdown renders cleanly in the terminal; don't paraphrase away specific numbers.
- **When the user asks follow-ups** (e.g. "is that expensive?", "which turn was slowest?"), answer from the same report or spot-check the JSONL with `Grep` — don't re-run `metrics.py` unless the session has changed.

## Typical first interaction

1. User says "inspect this session" or `/inspect-session`.
2. Run `python3 <skill-dir>/metrics.py` with no args → report on the current project's most recent session.
3. Present the markdown output. Flag any `[unavailable]` fields (e.g. cost when the model isn't in the price table) so the user knows the gap.
4. If the user asks about a different session, re-run with `--session-id` or a path.

## Reference files

- [reference/pricing.md](./reference/pricing.md) — how to update the embedded price table when Anthropic ships new models or adjusts rates.
