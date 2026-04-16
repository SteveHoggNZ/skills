# A/B testing a skill

A skill adds context and procedure to an agent's prompt. That's not free — every line of instruction spends attention on something, and not every skill earns it back. A/B testing is a cheap way to confirm that a skill actually makes the agent faster, more correct, or both.

This doc is generic. It applies to any skill in this repo, and to skills you develop for other marketplaces.

## When to run an A/B

- Before promoting a newly-written skill from "draft" to "documented".
- After any non-trivial change to `core.md` or the procedure it describes.
- When a skill accumulates runtime state (registries, caches, learned selectors) and you want to prove the state is doing useful work rather than just taking up disk.
- Whenever you suspect the skill is net-negative — e.g. the agent seems slower, or keeps asking clarifying questions that the skill's procedure should already answer.

Skip the A/B when the skill is a trivial wrapper (a one-liner slash command that just runs `npx foo`) — the ceremony outweighs the signal.

## Methodology

The core idea: spawn two subagents with the **same task** and compare how they do it. One gets the skill, one doesn't.

### 1. Pick a task that exercises what the skill claims to improve

A skill's value is in its claims. If the skill says "this lets you orient on a new codebase in 30 seconds", the task should be "tell me about this codebase". If it says "this remembers per-site UI quirks", the task should involve a site the skill has seen before.

Avoid tasks that are trivially solved either way — those test nothing. Avoid tasks that depend on the agent's general intelligence rather than the skill's content.

### 2. Eliminate shared state that would leak information between runs

Many skills interact with stateful systems: browser daemons, shell sessions, open files, API caches. If subagent A leaves residue that subagent B inherits, the test is invalid. Reset between runs:

- Close persistent daemons (e.g. `npx agent-browser close`).
- Clear caches the skill writes to, unless the cache IS the skill's value prop (then keep it warm for B, cold for A).
- Revert any test artifacts the first agent created.

### 3. Write two prompts

Both prompts describe the same task, same target, and same reporting format. They differ only in how the agent is directed to approach it.

**Baseline prompt (A):** minimal generic hints for whatever tools/CLI the task requires. No skill reference. The baseline is "a reasonably-equipped agent who has never seen this skill."

**Skill-enabled prompt (B):** points at the skill directory and instructs the agent to read `SKILL.md` first and follow its procedure. No other help.

Both prompts should end with the same reporting block, something like:

> Before finishing, also report:
> - Total <tool> invocations issued
> - Any dead-ends or incorrect assumptions you had to correct
> - Wall-clock feel: fast / medium / slow
> - [For B only] Specific pre-learned knowledge from the skill that saved you time, and anything you'd add to the skill next

### 4. Run sequentially when sharing stateful dependencies, in parallel otherwise

If both subagents drive the same browser daemon, database, or filesystem area, run them sequentially and reset between. If they're independent, run both in one message so they execute in parallel.

### 5. Compare across multiple axes, not just command count

Raw command count is a weak signal — a skill that reads three reference files first might issue more tool calls on turn one but fewer overall. Look at:

| Axis | What to notice |
|------|----------------|
| **Command count** | Meaningful only if the skill claims to reduce it. |
| **Dead-ends** | Wrong selector guesses, hangs, waiting for things that never happen. A skill with good gotchas should prevent these. |
| **Correctness of the result** | Did both agents report the same facts? A skill that speeds the agent up but gives wrong answers is a regression. |
| **Surprises caught** | Things the skill-enabled agent noticed and added to the skill's runtime state (e.g. a registry entry). These are proof the skill is self-improving. |
| **Knowledge specifically credited** | Ask the skill-enabled agent to name the sentence that saved them time. If they can't point to one, the content isn't earning its space. |
| **Wall-clock feel** | Subjective but useful — agents feel it when they're thrashing. |

### 6. Interpret first-use overhead honestly

On the agent's **first** encounter with a skill, it pays a one-time cost to read `SKILL.md`, the `core.md` procedure, and whatever reference files the procedure demands. This can make the first A/B look like a wash — B issues as many or more commands as A. That's expected.

The skill's value compounds across sessions:

- Gotchas prevent repeat-mistakes from turn two onward.
- Runtime state (like a per-site registry) accumulates.
- Conventions the skill surfaces ("all nav buttons use `aria-label`") save dozens of snapshots across a week.

If a first-use A/B shows parity, run a second A/B with the skill's state already populated — that's where the gap usually appears. If there's still no gap, the skill probably doesn't earn its context budget.

### 7. Watch for the self-correction signal

Skills that write runtime state (registries, learned caches, notes) have a second, subtler value: when B's skill-recorded knowledge is **wrong**, B discovers and fixes it. A would have hit the same wrong assumption silently and blamed the tool.

If your skill-enabled run comes back with "I corrected these two claims in the registry", that's a strong signal the skill is healthy — not a failure. The first run is the one that validates the recorded content; subsequent runs amortize the correction.

## Prompt templates

### Baseline (A)

```
You are testing <tool> (<one-line description>). This is a baseline test — you have only generic <tool> hints, no skill-specific knowledge.

## Target
<target>

## <tool> basics (all the help you get)
- <minimal list of commands/flags>

## Task
<the concrete thing to accomplish, with specific facts to report>

## Before you finish, also report
- Total <tool> invocations issued
- Any dead-ends / incorrect assumptions you had to correct
- Wall-clock feel: fast / medium / slow

Keep the response under 500 words. <Any safety caveats — e.g. "do not modify shared state", "close daemons at end">.
```

### Skill-enabled (B)

```
You are testing a skill at <absolute/path/to/skill/>.

## First step — BEFORE anything else
1. Read `SKILL.md` in the skill directory and follow its procedure end-to-end.
2. That procedure will tell you which other files to read (core.md, reference/*, any per-target state).
3. Follow the skill's invocation conventions exactly — including any wrapper scripts.

## Target
<same as A>

## Task
<identical to A>

## Before you finish, also report
- Total <tool> invocations issued (chained commands count as one)
- Specific pre-learned knowledge from the skill that saved you time, and what mistake it prevented
- Anything you'd add to the skill's runtime state next — any surprise not yet captured
- Wall-clock feel: fast / medium / slow

Keep the response under 500 words. <Same safety caveats as A>.
```

## What to do with the results

- **B wins clearly:** document the skill as validated. Keep the A/B transcript in case the signal is later disputed.
- **Parity on first use:** either run a warmed-state A/B (see step 6), or accept parity as "not worse" and re-test after the skill's runtime state has accumulated.
- **B loses:** the skill is overspending its context budget. Trim `core.md`, cut low-value reference material, and re-test. If trimming doesn't flip the result, the skill probably doesn't belong in the marketplace — retire it or convert it to plain docs.
- **B caught wrong claims in its own state:** expected and healthy. Verify the corrections landed, then call the test passed.

## Known limits of this method

- **n=1.** A single A/B is noisy. If the two runs are close, re-run or accept the uncertainty.
- **Agent variance.** The same subagent prompt can take different paths on different runs. Strong effects show through; marginal effects need more runs.
- **Selection bias on tasks.** Authors pick tasks that flatter their skills. If you want a harder test, have someone else design the task.
- **First-use overhead distorts the metric**, as covered above. Warmed-state A/B is the mitigation.
