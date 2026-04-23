# Inspect Session

Parse a Claude Code session JSONL transcript and report a concise metrics summary covering performance, cost, and activity shape.

## Why this skill exists

Claude Code stores a full session transcript as JSONL under `~/.claude/projects/<project-slug>/<session-id>.jsonl`. Every user message, assistant message, tool call, and usage block lands there. The file holds enough data to answer "how long did this session run, what did it cost, where did the tokens go?" — but it's noisy enough that eyeballing it doesn't work.

This skill wraps a deterministic Python script that reads the JSONL and emits a clean summary. No token spend on parsing; same answer every time; easy to pipe into other tools via `--json`.

## Output shape

Markdown by default:

```
# Session: 15f5fb6d-…
  Project:   /Users/one/Projects/SteveHoggNZ/skills
  Model:     claude-opus-4-7
  Started:   2026-04-18 14:03:22 UTC
  Ended:     2026-04-18 18:57:11 UTC
  Duration:  4h 53m 49s

## Activity
  User turns:       42
  Assistant turns:  89
  Tool calls:       231
  Slash commands:   6  (/shnz:docker-roast ×2, /shnz:agent-browser ×3, /shnz:narrative-commit ×1)

## Tokens
  Input (non-cached):     12,406
  Output:                 187,421
  Cache read:             4,218,902
  Cache creation (5m):    98,344
  Cache creation (1h):    12,015
  Cache hit rate:         97.3%

## Cost (USD)
  Input:                  $0.19
  Output:                 $14.06
  Cache read:             $6.33
  Cache creation:         $2.21
  ─────────────────────────────
  Total:                  $22.79

  Cost per user turn:     $0.54

## Tool-call breakdown
  Bash:         72
  Edit:         54
  Read:         41
  Grep:         22
  Agent:        14
  Glob:         13
  Write:        11
  (others, ≤4 each): 4 tools

## Assistant-turn latency
  min:     0.4s
  median:  2.1s
  p90:     11.7s
  max:     47.2s
```

`--json` emits the same structure as a single JSON object.

## Target resolution

In priority order:

1. **Explicit path** — `metrics.py /abs/path/to/session.jsonl` uses that file.
2. **Session ID (UUID)** — `metrics.py 15f5fb6d-…` searches `~/.claude/projects/*/15f5fb6d-….jsonl`.
3. **Default** — no args. Uses the most recent `*.jsonl` in `~/.claude/projects/<cwd-slugged>/`.

Slug rule for the default: the current working directory's absolute path with `/` replaced by `-`, and a leading `-` (e.g. `/Users/one/foo` → `-Users-one-foo`). That matches how Claude Code caches projects.

If no JSONL is found, the script exits non-zero with a message listing nearby candidate directories.

## Procedure

### 1. Resolve the target JSONL

Parse `ARGUMENTS`. Empty → default; one token that's a UUID → session-id lookup; one token that's a path → explicit file. Optional `--json` anywhere in args → JSON output. Unknown flags fail loudly.

### 2. Stream-parse

Read the JSONL line by line (sessions can be large — the current project's is 1,100+ lines and growing). For each record:

- `type: "user"` → user turn. Record `timestamp`; count `content[]` entries that are tool results separately.
- `type: "assistant"` → assistant turn. Record `timestamp`, `message.model`, `message.usage`, iterate `message.content[]` for `tool_use` entries (count by `name`).
- `type: "permission-mode"`, `file-history-snapshot`, `attachment` → skipped for metrics, but attachment sizes could be added later.

Slash commands appear as user messages whose content contains a `<command-name>…</command-name>` tag. Extract the command name via regex.

### 3. Compute metrics

- **Start / end / duration**: min and max of all record timestamps.
- **User / assistant turn counts**: record-type frequency.
- **Tool calls**: count `tool_use` content items across all assistant records; aggregate by `name`.
- **Token totals**: sum of each usage-block field across all assistant records. The `usage.cache_creation.ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens` fields break cache creation into the two TTLs that price differently.
- **Cache hit rate**: `cache_read / (cache_read + cache_creation + input_tokens)` as a percent.
- **Latency**: for each consecutive `(user → assistant)` pair, subtract timestamps. Emit min / median / p90 / max.
- **Cost**: for each assistant record, look up the model in the embedded price table and compute per-bucket cost. Sum across all assistant records so mid-session model switches (rare, but possible) price correctly.
- **Cost per user turn**: `total_cost / user_turns` when `user_turns > 0`.

### 4. Render

Markdown by default (readable in a terminal, pastes cleanly into a note or a chat message). `--json` serializes the full metrics object — every field the markdown view shows, plus a few the markdown elides for brevity (e.g. per-model token subtotals when multiple models appear).

### 5. Handle gaps explicitly

If a metric can't be computed, print `[unavailable]` with a short reason. Concrete cases:

- Model not in the price table → cost fields all `[unavailable: model <name> not in price table — see reference/pricing.md]`.
- No user turns → cost-per-turn `[unavailable: no user turns]`.
- Single-turn session → latency `[unavailable: need ≥ 2 assistant responses]`.

Never fabricate.

## Pricing

The price table is hardcoded in `metrics.py`. Keys on model name (exactly as it appears in `message.model` in the JSONL). Public Anthropic rates, expressed in **USD per 1M tokens**. See [reference/pricing.md](./reference/pricing.md) for the update flow.

Ephemeral 5m and 1h cache-creation tokens price differently; the script sums them into one "cache creation" line in the markdown for brevity but keeps the buckets separate in the JSON output.

## Invocation

```bash
# Default — most recent session in the current project
python3 <skill-dir>/metrics.py

# Specific session by UUID
python3 <skill-dir>/metrics.py 15f5fb6d-8170-4a51-90e6-0e4bfd82d7dc

# Specific JSONL path
python3 <skill-dir>/metrics.py ~/.claude/projects/-foo-bar/session.jsonl

# Machine-readable
python3 <skill-dir>/metrics.py --json | jq '.cost.total_usd'
```

Claude Code agents should invoke via `Bash` rather than re-implementing the parser.

## What NOT to do

- **Don't re-implement in the model's head.** The script is ~250 lines of stdlib Python. Calling it costs < 1s and no tokens. Hand-parsing 1,000-line JSONLs in conversation costs thousands of tokens and invites rounding errors.
- **Don't invent numbers when a field is missing.** Prefer `[unavailable]` with a reason over a guess.
- **Don't cache results.** Sessions grow. If the user re-asks on the same session mid-conversation, re-run — the numbers have moved.
- **Don't log the script's output to a file without asking.** The user may want a one-shot terminal print and nothing committed anywhere. A `--out <path>` flag is a reasonable future addition; don't bolt it on silently.

## Iteration

Good candidate for `skill-iterate` once a few real sessions have been inspected. Likely friction points:

- Price table drift as Anthropic ships new models.
- Useful metrics not in v1 (e.g. time spent on specific tools, cost of a single turn).
- Session aggregation across multiple JSONLs (closer to `monthly-insights`, but finer-grained).
