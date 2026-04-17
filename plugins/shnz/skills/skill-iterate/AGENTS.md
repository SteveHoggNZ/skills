# Skill Iterate (Codex adapter)

When the user asks to iterate, improve, polish, optimize, or refine a skill, follow the procedure in [core.md](./core.md).

## Codex specifics

- **Spawn the probe subagent** using your host's subagent invocation mechanism. Fill the template at [reference/subagent-prompt.md](./reference/subagent-prompt.md) and pass the populated prompt to the subagent.
- **Read the target skill's files** with your available file-reading tools before spawning the probe — you can't interpret the report without knowing the starting state.
- **Apply edits surgically.** Prefer small, targeted patches over rewrites; preserve the target skill's prose voice.
- **Do not apply edits unilaterally.** Present a diff-style summary to the user and wait for explicit approval.

## Stopping

Convergence: probe reports `none` for both friction and edits two iterations in a row. Beyond that, switch task surface or stop.
