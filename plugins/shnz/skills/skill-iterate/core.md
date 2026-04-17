# Skill Iterate

Drive a target skill toward its **optimal floor** by running a probe subagent against a representative task, collecting a structured report, applying concrete edits, and repeating until the subagent reports no further friction.

## Relationship to other skill-level tooling

- [`docs/AB_TESTING.md`](../../../../docs/AB_TESTING.md) answers **"does this skill earn its context cost?"** — a one-shot, with-vs-without comparison used before merging a new skill.
- This skill (`skill-iterate`) answers **"is this skill as good as it can be?"** — a repeated loop used after the A/B passes, to polish the skill against a specific task surface until it converges.

Both are complementary. Don't use `skill-iterate` on a skill that hasn't passed its A/B; you'll iterate something that shouldn't exist.

## Naming convention (meta-skills)

Skills in this marketplace that operate on other skills use the `skill-*` prefix (this one is `skill-iterate`; future additions might be `skill-review`, `skill-doctor`, etc.). Non-meta skills (`dump`, `agent-browser`, `narrative-commit`) do not use the prefix.

## Procedure

One invocation = one iteration. The user paces the loop.

### 1. Gather inputs

Ask the user (or read from context) for:

- **Target skill path** — absolute path to the skill directory, e.g. `/abs/path/plugins/shnz/skills/agent-browser/`.
- **Task description** — a concrete end-to-end task that exercises the skill's claims. Bad: "try the skill out". Good: "log into localhost:4173 as steve+user, create a channel called X, add agent Y, @-mention them and send a message".
- **Iteration number** — default 1; if the user is continuing an earlier loop, ask which iteration this is and whether to inherit prior findings.

If the skill hasn't been A/B tested yet, flag it and recommend `docs/AB_TESTING.md` first rather than iterating.

### 2. Understand starting state

Before spawning the probe, read the target skill's files so you can evaluate the report:

- `SKILL.md`, `core.md`, any `AGENTS.md` / `copilot-instructions.md` adapters.
- Every file under `reference/` (these are the shared catalogs that probe subagents will consult).
- If the skill has a runtime-state directory (e.g. `.registry/`), list its contents and peek at any entries relevant to the task — but do **not** edit runtime state; the subagent may update it autonomously.

Optionally run `git log -n 10 -- <skill-dir>` to see whether the skill has been iterated before; informs how aggressive to be with proposed edits.

### 3. Spawn the probe subagent

Use your host's subagent tool (in Claude Code: the `Agent` tool, `general-purpose` subagent_type) with the template at [`reference/subagent-prompt.md`](./reference/subagent-prompt.md), filling in:

- The skill's absolute path.
- The task description.
- Any credentials or prerequisites.
- The structured report format (the template already demands it).

The subagent does the task and returns a report with: invocation count, cited time-savers, friction points, concrete edit recommendations, and a wall-clock subjective rating.

### 4. Interpret the report

Classify each recommendation before showing the user:

| Class | What it is | Handling |
|-------|-----------|----------|
| **Concrete fix** | Specific file + line + suggested change; pre-empts a real mistake the next agent would make | Candidate for this iteration |
| **Operator error** | The subagent made a mistake that isn't the skill's fault (e.g. misread their own notes) | Note it, don't apply |
| **Unverified claim** | Subagent asserts a fact about the site/tool that contradicts the skill but hasn't been verified | Probe it directly before applying; do not trust blindly |
| **Stylistic / polish** | Edits to prose, formatting, duplication | Apply sparingly; these rarely change subagent behavior |

Also check for **false positives** in the subagent's framing — e.g. "site has no `aria-label`" framed as a site bug when it's actually correct a11y. The target skill author (or site author) may have already flagged that this is expected. Re-read the skill's own files before accepting a claim that contradicts them.

### 5. Present proposed edits to the user

Show a diff-style list:

```
Edit 1 — path/to/file.md
  Section: "Add an agent to the current channel" step 3
  Reason: Subagent's silent-add-member hang — clicking unfiltered list silently no-ops
  Change: require filtering the search box before clicking a row.

Edit 2 — ...
```

The user approves, rejects, or modifies each. Do not apply unilaterally.

### 6. Apply approved edits

Use precise edits (`Edit` tool with surgical `old_string`/`new_string`). Don't rewrite whole sections. Keep the intent of the existing prose; pattern-match the surrounding voice.

If the target skill uses a versioning / visit-count pattern (e.g. agent-browser's `visit_count` in registry frontmatter), bump appropriately per the target skill's own rules.

### 7. Report iteration result

Present a short summary:

- Invocation count this run (compared to prior run if known)
- Friction count
- Edits applied (with files touched)
- Wall-clock feel
- Classification of any leftover recommendations not applied

If the user is iterating in a series, maintain a running trajectory table across iterations (iter → invocations → friction → new issues → fixes applied).

### 8. Offer another iteration

Ask explicitly. Convergence signal: **two consecutive iterations where the subagent reports `none` for both friction and recommended edits**. At that point declare the skill converged for the task surface and suggest either:

- Running `skill-iterate` against the same skill with a **different task surface** to shake out untested paths; or
- Stopping and marking the skill as stable.

Diminishing returns signal: invocation count stops dropping AND new discoveries plateau for 2+ iterations. Time to stop even if not formally converged.

## Stopping conditions

Stop early (before convergence) if any of:

- Invocation count rises for 2+ iterations (you're adding overhead, not removing it).
- Proposed edits start contradicting recent prior edits (the skill is oscillating).
- The user runs out of patience or token budget (each iteration costs real tokens).

## What NOT to iterate on

- Skills that haven't passed an A/B (see `docs/AB_TESTING.md` first — the skill may not deserve to exist).
- Skills whose task surface you don't have a reproducible probe for (this loop needs a concrete, replayable task).
- Skills with shared mutable state that can't be reset between iterations (results will be noisy).
