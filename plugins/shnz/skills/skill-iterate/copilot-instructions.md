# Skill Iterate (Copilot adapter)

When the user asks to iterate, improve, polish, optimize, or refine a skill, follow the procedure in [core.md](./core.md).

## Copilot specifics

- **Spawn the probe subagent** via VS Code's agent / subagent mechanism if available. Fill the template at [reference/subagent-prompt.md](./reference/subagent-prompt.md) and pass the populated prompt. If VS Code can't spawn a nested agent directly, have the user start a second Copilot session with the filled prompt and paste the report back.
- **Open the target skill's files** in VS Code and review each before spawning the probe — you can't interpret the report without knowing the starting state.
- **Apply edits surgically** using VS Code's edit-applying capabilities. Small, targeted patches preserve the skill's voice.
- **Do not apply edits unilaterally.** Present a diff-style summary to the user and wait for explicit approval.

## Stopping

Convergence: probe reports `none` for both friction and edits two iterations in a row. Beyond that, switch task surface or stop.
