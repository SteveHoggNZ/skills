# Probe subagent prompt template

Fill the placeholders and paste the filled prompt into your host's subagent tool. The structured report at the end is mandatory — don't weaken it; that's where the next iteration's signal comes from.

---

## Template

```
You are testing a skill by performing a concrete task and reporting on efficiency.

## Skill under test
{{SKILL_ABSOLUTE_PATH}}

## First step — BEFORE doing anything else
1. Read `SKILL.md` in the skill directory and follow its procedure end-to-end.
2. Read the files it directs you to (`core.md`, `reference/*`, any runtime-state files the procedure mentions).
3. Follow the skill's invocation conventions exactly. If the skill has a specific wrapper pattern or command-file convention, use it — do not shortcut around it.

## Task
{{CONCRETE_TASK_DESCRIPTION}}

## Prerequisites / credentials (if any)
{{PREREQUISITES}}

## Iteration context (optional)
This is iteration {{N}} of an optimization loop. Prior iterations have already addressed: {{PRIOR_FIXES_BRIEF}}. Do NOT treat prior fixes as still-open issues. The calling agent wants to know what's NEW in this run — new friction, new recommendations, or confirmation that the skill has converged on this task surface.

## Mandatory structured report (keep under 600 words)

1. **Outcome** — one sentence: did the task succeed end-to-end?
2. **Total invocations** — count of top-level calls to the skill's main tool/CLI. Chained operations within one invocation count as one.
3. **Step-by-step breakdown** — one line per invocation, terse. This lets the caller see where overhead is.
4. **Registry / reference content that actively saved a mistake** — quote the exact line(s) from the skill's files that steered you correctly. Be specific: "I'd have clicked X if not for line Y in file Z."
5. **Friction encountered** — every point where you had to re-read, re-derive, or recover from an unexpected state. Distinguish:
   - Skill defect (missing / wrong / ambiguous guidance)
   - Operator error (your mistake, not the skill's fault)
   - Unverified claim (skill says X; your observation disagreed — but you aren't sure which is right)
6. **Concrete edit recommendations** — for each recommendation:
   - File path (absolute)
   - Section or approximate line
   - What to change and why
   Do NOT edit the skill files yourself; the calling agent reviews before applying.
7. **Wall-clock feel** — fast / medium / slow, with a sentence of why.
8. **If both #5 and #6 are empty, say "none" explicitly for each.**

## Safety / etiquette

- Do not send messages, make purchases, or take destructive actions unless the task explicitly requires them and you're on a non-shared instance.
- Clean up per the skill's conventions (close daemons, remove temp files if the skill says so).
- Keep your response under the word limit; verbosity hides the signal.
```

---

## Placeholders to fill

| Placeholder | What to put |
|---|---|
| `{{SKILL_ABSOLUTE_PATH}}` | Absolute path to the target skill directory |
| `{{CONCRETE_TASK_DESCRIPTION}}` | The reproducible end-to-end task |
| `{{PREREQUISITES}}` | Credential paths, environment details, or "none" |
| `{{N}}` | Iteration number (1, 2, 3…) |
| `{{PRIOR_FIXES_BRIEF}}` | One-line summary of prior iterations' fixes, or "none — first iteration" |

## Tips

- **Keep the task identical across iterations** when measuring convergence. If the task varies, you're measuring noise.
- **Close out any stateful dependencies between iterations** (browser daemons, database connections, server state). The probe must start from the same place.
- **If the skill writes to runtime state** (caches, registries, notes files), the subagent may update that state during its run. That's fine — it's how the skill self-corrects — but record the delta in the iteration's summary.
- **Don't ask the subagent to propose subjective/stylistic changes**. The report focuses on friction and concrete fixes; polish iterations dilute the signal.
