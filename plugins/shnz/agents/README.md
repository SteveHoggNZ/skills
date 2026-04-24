# Agents

This directory is reserved for **plugin-scoped agent definitions** — orchestrators that span multiple skills or manage complex multi-step workflows that don't belong to a single skill.

## When to add an agent here

- The workflow coordinates **two or more skills** in a non-trivial way.
- The logic is too heavy to live in a single `core.md`.
- The agent manages persistent state across skill invocations.

## When NOT to add an agent here

- A single skill's internal sub-agent (e.g. a probe subagent spawned by `skill-iterate`) — that belongs in the skill's own directory.
- A thin runtime adapter — those are `AGENTS.md` / `copilot-instructions.md` files inside each skill directory.

## No agents yet

No plugin-scoped agents are defined yet. Individual skills handle their own scope.
