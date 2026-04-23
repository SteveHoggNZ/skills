#!/usr/bin/env python3
"""Inspect a Claude Code session JSONL transcript and report metrics.

Usage:
    metrics.py                      # most recent session in current project
    metrics.py <session-uuid>       # specific session by id
    metrics.py <path/to/file.jsonl> # explicit path
    metrics.py --json               # JSON output instead of markdown
    metrics.py --help

Stdlib only. See core.md for the field-by-field spec.

The file is named metrics.py (not inspect.py) to avoid shadowing Python's
stdlib `inspect` module, which `dataclasses` imports — a same-directory
`inspect.py` would cause a circular-import failure at startup.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ─── Price table (USD per 1M tokens) ────────────────────────────────────────
# Keys match `message.model` as stored in the JSONL. Update when Anthropic
# ships new models or adjusts rates — see reference/pricing.md.
#
# "input"    — non-cached input tokens
# "output"   — output tokens
# "cache_r"  — cache read
# "cache_w5" — cache creation, 5-minute TTL
# "cache_w1" — cache creation, 1-hour TTL
PRICES: dict[str, dict[str, float]] = {
    # Opus 4.x family
    "claude-opus-4-7":  {"input": 15.00, "output": 75.00, "cache_r": 1.50, "cache_w5": 18.75, "cache_w1": 30.00},
    "claude-opus-4-6":  {"input": 15.00, "output": 75.00, "cache_r": 1.50, "cache_w5": 18.75, "cache_w1": 30.00},
    "claude-opus-4-5":  {"input": 15.00, "output": 75.00, "cache_r": 1.50, "cache_w5": 18.75, "cache_w1": 30.00},
    # Sonnet 4.x
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_r": 0.30, "cache_w5": 3.75, "cache_w1": 6.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00, "cache_r": 0.30, "cache_w5": 3.75, "cache_w1": 6.00},
    # Haiku 4.5
    "claude-haiku-4-5":              {"input": 1.00, "output": 5.00, "cache_r": 0.10, "cache_w5": 1.25, "cache_w1": 2.00},
    "claude-haiku-4-5-20251001":     {"input": 1.00, "output": 5.00, "cache_r": 0.10, "cache_w5": 1.25, "cache_w1": 2.00},
}


# ─── Target resolution ──────────────────────────────────────────────────────

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
CMD_RE = re.compile(r"<command-name>\s*(/[^<\s]+)\s*</command-name>")


def cwd_slug(cwd: str) -> str:
    """Replicate Claude Code's project-slug rule: abspath with / -> -."""
    return "-" + cwd.strip("/").replace("/", "-")


def resolve_target(arg: str | None) -> Path:
    """Return a Path to the JSONL to inspect, or raise."""
    home = Path.home()

    # 1. Explicit path.
    if arg and ("/" in arg or arg.endswith(".jsonl")):
        p = Path(arg).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"error: path not found: {p}")
        return p

    # 2. Session UUID.
    if arg and UUID_RE.match(arg):
        projects = home / ".claude" / "projects"
        hits = list(projects.glob(f"*/{arg}.jsonl"))
        if not hits:
            raise SystemExit(f"error: no JSONL found for session {arg} under {projects}")
        # If multiple (unlikely), prefer the one whose project slug matches cwd.
        if len(hits) > 1:
            mine = projects / cwd_slug(os.getcwd())
            for h in hits:
                if h.parent == mine:
                    return h
        return hits[0]

    # 3. Default: most recent in current project.
    project_dir = home / ".claude" / "projects" / cwd_slug(os.getcwd())
    if not project_dir.exists():
        # Suggest neighbours.
        neighbours = sorted((home / ".claude" / "projects").glob("*"))[:10]
        hint = "\n  ".join(str(n.name) for n in neighbours)
        raise SystemExit(
            f"error: no project cache at {project_dir}\n"
            f"nearby projects:\n  {hint}\n"
            f"pass an explicit --session-id or path, or run from the matching project dir"
        )
    jsonls = sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsonls:
        raise SystemExit(f"error: no *.jsonl in {project_dir}")
    return jsonls[0]


# ─── Parsing ────────────────────────────────────────────────────────────────

@dataclass
class Metrics:
    session_id: str = ""
    cwd: str = ""
    models: set[str] = field(default_factory=set)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    user_turns: int = 0
    assistant_turns: int = 0
    tool_calls: int = 0
    tool_breakdown: dict[str, int] = field(default_factory=dict)
    slash_commands: dict[str, int] = field(default_factory=dict)

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_5m_tokens: int = 0
    cache_write_1h_tokens: int = 0

    # For latency: list of (user_ts, next_assistant_ts) pairs → delta in seconds.
    latencies: list[float] = field(default_factory=list)

    # Per-model token totals (for per-model cost split when multiple models appear).
    per_model_tokens: dict[str, dict[str, int]] = field(default_factory=dict)


def parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    # Claude Code timestamps are ISO 8601 with "Z".
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def extend_window(m: Metrics, ts: datetime | None) -> None:
    if not ts:
        return
    if m.started_at is None or ts < m.started_at:
        m.started_at = ts
    if m.ended_at is None or ts > m.ended_at:
        m.ended_at = ts


def bucket_for(model: str, m: Metrics) -> dict[str, int]:
    b = m.per_model_tokens.setdefault(
        model,
        {"input": 0, "output": 0, "cache_r": 0, "cache_w5": 0, "cache_w1": 0},
    )
    return b


def parse(path: Path) -> Metrics:
    m = Metrics()
    last_user_ts: datetime | None = None

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate a malformed tail

            rtype = rec.get("type")
            ts = parse_ts(rec.get("timestamp"))
            extend_window(m, ts)

            if not m.session_id:
                m.session_id = rec.get("sessionId", "") or m.session_id
            if not m.cwd:
                m.cwd = rec.get("cwd", "") or m.cwd

            if rtype == "user":
                # A "user" record may be a real user turn OR a tool result piped
                # back as a user message. Tool-result records have content items
                # where type == "tool_result"; we only count the record as a
                # user turn when at least one content item is text (i.e. a
                # human or synthetic user utterance).
                content = rec.get("message", {}).get("content", [])
                is_real_user = False
                if isinstance(content, str):
                    is_real_user = True
                    # Scan for slash commands in the string form.
                    for cmd in CMD_RE.findall(content):
                        m.slash_commands[cmd] = m.slash_commands.get(cmd, 0) + 1
                elif isinstance(content, list):
                    has_text = any(
                        isinstance(c, dict) and c.get("type") in ("text", None) and c.get("text")
                        for c in content
                    )
                    is_tool_result_only = all(
                        isinstance(c, dict) and c.get("type") == "tool_result"
                        for c in content
                    ) and len(content) > 0
                    is_real_user = has_text and not is_tool_result_only
                    # Slash commands live in text content.
                    for c in content:
                        if isinstance(c, dict) and c.get("text"):
                            for cmd in CMD_RE.findall(c.get("text", "")):
                                m.slash_commands[cmd] = m.slash_commands.get(cmd, 0) + 1

                if is_real_user:
                    m.user_turns += 1
                    last_user_ts = ts

            elif rtype == "assistant":
                m.assistant_turns += 1
                msg = rec.get("message", {})
                model = msg.get("model") or ""
                # Claude Code emits some assistant records with model="<synthetic>"
                # for non-billable meta events (compaction prompts, etc.). Exclude
                # them from model-list and pricing so the report isn't noisy.
                is_synthetic = model.startswith("<") and model.endswith(">")
                if model and not is_synthetic:
                    m.models.add(model)

                usage = msg.get("usage", {}) or {}
                inp = int(usage.get("input_tokens") or 0)
                out = int(usage.get("output_tokens") or 0)
                cr  = int(usage.get("cache_read_input_tokens") or 0)
                # Prefer the nested breakdown when present; fall back to the
                # flat cache_creation_input_tokens if only that is available.
                cc = usage.get("cache_creation") or {}
                cw5 = int(cc.get("ephemeral_5m_input_tokens") or 0)
                cw1 = int(cc.get("ephemeral_1h_input_tokens") or 0)
                if cw5 == 0 and cw1 == 0:
                    cw5 = int(usage.get("cache_creation_input_tokens") or 0)

                m.input_tokens         += inp
                m.output_tokens        += out
                m.cache_read_tokens    += cr
                m.cache_write_5m_tokens += cw5
                m.cache_write_1h_tokens += cw1

                if model and not is_synthetic:
                    b = bucket_for(model, m)
                    b["input"]   += inp
                    b["output"]  += out
                    b["cache_r"] += cr
                    b["cache_w5"] += cw5
                    b["cache_w1"] += cw1

                # Tool-use content items (one per tool call this turn).
                for c in msg.get("content", []) or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        name = c.get("name") or "?"
                        m.tool_calls += 1
                        m.tool_breakdown[name] = m.tool_breakdown.get(name, 0) + 1

                # Latency: if we have both a preceding user ts and this ts.
                if ts and last_user_ts and ts > last_user_ts:
                    m.latencies.append((ts - last_user_ts).total_seconds())
                    last_user_ts = None  # only the *first* assistant reply counts

    return m


# ─── Costing ────────────────────────────────────────────────────────────────

def cost_for(model: str, tokens: dict[str, int]) -> dict[str, float] | None:
    p = PRICES.get(model)
    if not p:
        return None
    return {
        "input":    tokens["input"]    * p["input"]    / 1_000_000,
        "output":   tokens["output"]   * p["output"]   / 1_000_000,
        "cache_r":  tokens["cache_r"]  * p["cache_r"]  / 1_000_000,
        "cache_w5": tokens["cache_w5"] * p["cache_w5"] / 1_000_000,
        "cache_w1": tokens["cache_w1"] * p["cache_w1"] / 1_000_000,
    }


def aggregate_cost(m: Metrics) -> tuple[dict[str, float] | None, list[str]]:
    """Return (totals or None if no pricing, list of models missing from table)."""
    totals = {"input": 0.0, "output": 0.0, "cache_r": 0.0, "cache_w5": 0.0, "cache_w1": 0.0}
    missing = []
    any_priced = False
    for model, toks in m.per_model_tokens.items():
        c = cost_for(model, toks)
        if c is None:
            missing.append(model)
            continue
        any_priced = True
        for k in totals:
            totals[k] += c[k]
    if not any_priced:
        return (None, missing)
    return (totals, missing)


# ─── Rendering ──────────────────────────────────────────────────────────────

def fmt_duration(td: float) -> str:
    s = int(td)
    h, rem = divmod(s, 3600)
    mi, se = divmod(rem, 60)
    parts = []
    if h:  parts.append(f"{h}h")
    if mi or h: parts.append(f"{mi}m")
    parts.append(f"{se}s")
    return " ".join(parts)


def fmt_ts(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def fmt_money(n: float) -> str:
    return f"${n:,.2f}" if abs(n) >= 0.01 else f"${n:,.4f}"


def render_markdown(m: Metrics, path: Path) -> str:
    lines: list[str] = []

    # ── Header ──
    lines.append(f"# Session: {m.session_id or '[unknown]'}")
    lines.append(f"  File:      {path}")
    lines.append(f"  Project:   {m.cwd or '[unknown]'}")
    if m.models:
        label = sorted(m.models)[0] if len(m.models) == 1 else ", ".join(sorted(m.models))
        lines.append(f"  Model{'s' if len(m.models) > 1 else ' ':8} {label}")
    if m.started_at:
        lines.append(f"  Started:   {fmt_ts(m.started_at)}")
    if m.ended_at:
        lines.append(f"  Ended:     {fmt_ts(m.ended_at)}")
    if m.started_at and m.ended_at:
        lines.append(f"  Duration:  {fmt_duration((m.ended_at - m.started_at).total_seconds())}")

    # ── Activity ──
    lines.append("")
    lines.append("## Activity")
    lines.append(f"  User turns:       {m.user_turns}")
    lines.append(f"  Assistant turns:  {m.assistant_turns}")
    lines.append(f"  Tool calls:       {m.tool_calls}")
    if m.slash_commands:
        total = sum(m.slash_commands.values())
        top = sorted(m.slash_commands.items(), key=lambda kv: -kv[1])
        pretty = ", ".join(f"{k} ×{v}" for k, v in top)
        lines.append(f"  Slash commands:   {total}  ({pretty})")
    else:
        lines.append(f"  Slash commands:   0")

    # ── Tokens ──
    total_input = m.input_tokens + m.cache_read_tokens + m.cache_write_5m_tokens + m.cache_write_1h_tokens
    hit_rate = (m.cache_read_tokens / total_input * 100) if total_input else 0.0
    lines.append("")
    lines.append("## Tokens")
    lines.append(f"  Input (non-cached):    {m.input_tokens:>12,}")
    lines.append(f"  Output:                {m.output_tokens:>12,}")
    lines.append(f"  Cache read:            {m.cache_read_tokens:>12,}")
    lines.append(f"  Cache creation (5m):   {m.cache_write_5m_tokens:>12,}")
    lines.append(f"  Cache creation (1h):   {m.cache_write_1h_tokens:>12,}")
    lines.append(f"  Cache hit rate:        {hit_rate:>11.1f}%")

    # ── Cost ──
    totals, missing = aggregate_cost(m)
    lines.append("")
    lines.append("## Cost (USD)")
    if totals is None:
        lines.append(f"  [unavailable: no priced models — missing from table: {', '.join(missing) or 'none'}]")
        lines.append(f"  See reference/pricing.md to add them.")
    else:
        lines.append(f"  Input:            {fmt_money(totals['input'])}")
        lines.append(f"  Output:           {fmt_money(totals['output'])}")
        lines.append(f"  Cache read:       {fmt_money(totals['cache_r'])}")
        lines.append(f"  Cache creation:   {fmt_money(totals['cache_w5'] + totals['cache_w1'])}")
        grand = sum(totals.values())
        lines.append(f"  " + "─" * 32)
        lines.append(f"  Total:            {fmt_money(grand)}")
        if m.user_turns > 0:
            lines.append("")
            lines.append(f"  Cost per user turn: {fmt_money(grand / m.user_turns)}")
        if missing:
            lines.append(f"  [partial: {', '.join(missing)} not in price table — excluded]")

    # ── Tool breakdown ──
    if m.tool_breakdown:
        lines.append("")
        lines.append("## Tool-call breakdown")
        ordered = sorted(m.tool_breakdown.items(), key=lambda kv: -kv[1])
        # Show top 7 by count; collapse rest.
        top = ordered[:7]
        rest = ordered[7:]
        max_len = max(len(k) for k, _ in top)
        for k, v in top:
            lines.append(f"  {k.ljust(max_len)}  {v:>4}")
        if rest:
            rest_total = sum(v for _, v in rest)
            lines.append(f"  (others, {len(rest)} tools, ≤{rest[0][1]} each): {rest_total}")

    # ── Latency ──
    lines.append("")
    lines.append("## Assistant-turn latency")
    if len(m.latencies) >= 2:
        lats = sorted(m.latencies)
        p90 = lats[max(0, int(len(lats) * 0.9) - 1)]
        lines.append(f"  min:     {min(lats):.1f}s")
        lines.append(f"  median:  {statistics.median(lats):.1f}s")
        lines.append(f"  p90:     {p90:.1f}s")
        lines.append(f"  max:     {max(lats):.1f}s")
        lines.append(f"  samples: {len(lats)}")
    else:
        lines.append(f"  [unavailable: need ≥ 2 assistant responses; got {len(m.latencies)}]")

    return "\n".join(lines)


def render_json(m: Metrics, path: Path) -> str:
    totals, missing = aggregate_cost(m)
    total_input = m.input_tokens + m.cache_read_tokens + m.cache_write_5m_tokens + m.cache_write_1h_tokens
    lats = sorted(m.latencies)

    out: dict[str, Any] = {
        "session_id": m.session_id or None,
        "file": str(path),
        "project_cwd": m.cwd or None,
        "models": sorted(m.models),
        "started_at": m.started_at.isoformat() if m.started_at else None,
        "ended_at": m.ended_at.isoformat() if m.ended_at else None,
        "duration_sec": (m.ended_at - m.started_at).total_seconds() if m.started_at and m.ended_at else None,
        "activity": {
            "user_turns": m.user_turns,
            "assistant_turns": m.assistant_turns,
            "tool_calls": m.tool_calls,
            "slash_commands": m.slash_commands,
        },
        "tokens": {
            "input": m.input_tokens,
            "output": m.output_tokens,
            "cache_read": m.cache_read_tokens,
            "cache_write_5m": m.cache_write_5m_tokens,
            "cache_write_1h": m.cache_write_1h_tokens,
            "cache_hit_rate": (m.cache_read_tokens / total_input) if total_input else None,
        },
        "per_model_tokens": m.per_model_tokens,
        "tool_breakdown": m.tool_breakdown,
        "latency_sec": {
            "samples": len(lats),
            "min": min(lats) if lats else None,
            "median": statistics.median(lats) if lats else None,
            "p90": (lats[max(0, int(len(lats) * 0.9) - 1)] if len(lats) >= 2 else None),
            "max": max(lats) if lats else None,
        },
        "cost_usd": None if totals is None else {
            "input": round(totals["input"], 4),
            "output": round(totals["output"], 4),
            "cache_read": round(totals["cache_r"], 4),
            "cache_write_5m": round(totals["cache_w5"], 4),
            "cache_write_1h": round(totals["cache_w1"], 4),
            "total": round(sum(totals.values()), 4),
            "per_user_turn": round(sum(totals.values()) / m.user_turns, 4) if m.user_turns else None,
        },
        "pricing_gaps": missing,
    }
    return json.dumps(out, indent=2, default=str)


# ─── Entry point ────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    args = list(argv[1:])
    as_json = False
    for flag in ("--json", "-j"):
        if flag in args:
            as_json = True
            args.remove(flag)

    if "--help" in args or "-h" in args:
        print(__doc__, file=sys.stderr)
        return 0

    target_arg = args[0] if args else None
    if len(args) > 1:
        print(f"error: too many arguments: {args}", file=sys.stderr)
        return 2

    path = resolve_target(target_arg)
    m = parse(path)
    print(render_json(m, path) if as_json else render_markdown(m, path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
