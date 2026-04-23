# Pricing table

`metrics.py` has a hardcoded `PRICES` dict that maps a model name (as stored in `message.model` in the JSONL) to per-bucket rates in **USD per 1 million tokens**.

## When to update

- Anthropic ships a new model (e.g. `claude-opus-5-0`, `claude-sonnet-4-7`).
- Anthropic publishes a price change for an existing model.
- You inspect a session and the report shows `[unavailable: no priced models — missing from table: <name>]` or `[partial: <name> not in price table — excluded]`.

## How to update

Edit the `PRICES` dict near the top of `metrics.py`. Each entry has five keys:

```python
"claude-opus-4-7": {
    "input":    15.00,  # non-cached input tokens, $/MTok
    "output":   75.00,  # output tokens, $/MTok
    "cache_r":   1.50,  # cache READ (hit), $/MTok
    "cache_w5": 18.75,  # cache CREATION, 5-minute TTL, $/MTok
    "cache_w1": 30.00,  # cache CREATION, 1-hour TTL,   $/MTok
},
```

If a model aliases another (same prices, different name — common during rollouts), just add a second entry pointing to the same values. Don't try to deduplicate via dict merging; the explicit entry is easier to read and easier to delete later.

## Finding the canonical numbers

Current Anthropic pricing: <https://www.anthropic.com/pricing#api>.

The "cache writes" price depends on the TTL:
- 5-minute cache (the default): typically ~1.25× the input rate.
- 1-hour cache (opt-in via `cache_control.ttl`): typically ~2× the input rate.

Cache reads are typically ~0.1× the input rate.

If a rate for a specific TTL is unpublished, **underestimate it** — set `cache_w1` no lower than `cache_w5 × 1.6`. Under-reporting cost is worse than over-reporting; the user is calibrating their budget against your output.

## What NOT to do

- **Don't guess** at prices for a model you can't find public numbers for. Leave it out of the table and let the script report `[unavailable]`. A wrong number looks like a confident number.
- **Don't mix currencies.** All values are USD. If the user wants another currency, apply the FX conversion downstream (e.g. pipe `--json | jq '.cost_usd.total * 1.65'` for AUD).
- **Don't round.** Use the exact published rate. Rounding accumulates over a long session.
- **Don't add "estimated" models with `null` fields.** The script expects all five keys; missing keys crash at cost time.

## Verifying a change

After editing `PRICES`, run the script against a known session. The "Cost (USD)" section should render without `[unavailable]` or `[partial]` for the model you just added.

```bash
python3 metrics.py <some-session-id>
```

Rough sanity check: for a typical Claude Code session on Opus 4.x, cache reads dominate — expect cache-read cost to be ~30–50% of the total. If your numbers show cache-read cost swamping everything else (>80%), you may have a missing digit on a non-cache rate.
