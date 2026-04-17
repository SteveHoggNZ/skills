---
name: skill-iterate
description: "Polish a target skill toward its optimal floor by running a probe subagent on a representative task, collecting a structured report, applying concrete edits, and repeating until convergence. Use when the user asks to 'iterate on a skill', 'improve a skill', 'optimize a skill', 'tune a skill', 'refine a skill', 'find friction in a skill', or similar meta-skill operations. One invocation = one iteration; user paces the loop."
---

<!-- Claude Code adapter — the canonical procedure lives in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Claude Code specifics

- **Spawn the probe subagent with the `Agent` tool**, `subagent_type: general-purpose`. Fill the template at [reference/subagent-prompt.md](./reference/subagent-prompt.md) and pass the fully-populated prompt as the `prompt` argument.
- **Read the target skill's files** with `Read` before spawning the probe. At minimum: `SKILL.md`, `core.md`, every `reference/*.md`, and any runtime-state files mentioned by the skill's own procedure. You can't interpret the probe's report without knowing the starting state.
- **Apply edits with `Edit`** (surgical `old_string`/`new_string`) rather than `Write`. Small, targeted patches preserve the skill's voice and make diffs reviewable.
- **Track progress with `TodoWrite`** — one todo per approved edit makes the iteration auditable.
- **Do not apply edits unilaterally.** Present the proposed diff to the user and wait for explicit approval before touching the target skill's files.

## When to use vs other meta-work

- **Use this skill** after a skill has passed its A/B (see [`docs/AB_TESTING.md`](../../../../docs/AB_TESTING.md)) and you want to polish it against a specific task surface.
- **Don't use this skill** to verify whether a new skill is worth keeping — that's what A/B testing is for.
- **Don't use this skill** on a skill you can't probe with a reproducible end-to-end task.

## Stopping

Declare convergence when the probe subagent reports `none` for both friction AND recommended edits **two iterations in a row**. Beyond that, either pick a different task surface or stop.
