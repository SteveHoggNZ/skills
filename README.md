# shnz-skills

Private skill marketplace for agentic automation — a small, opinionated collection of Claude Code (and adapter-compatible) skills that I use day-to-day.

## Structure

```
/
├── marketplace.json          # marketplace manifest consumed by Claude Code
├── plugins/
│   └── shnz/                 # the plugin bundling all skills in this repo
│       └── skills/
│           ├── dump/             # repomix-based context bundling
│           ├── agent-browser/    # browser automation CLI + per-site registry
│           └── narrative-commit/ # split uncommitted changes into a clean conventional-commits sequence
└── docs/                     # cross-cutting process notes
    └── AB_TESTING.md         # how to validate that a skill actually helps
```

Each skill directory follows the same layout:

- `SKILL.md` — Claude Code entry point (frontmatter + pointer to `core.md`).
- `core.md` — canonical, agent-agnostic procedure.
- `AGENTS.md` / `copilot-instructions.md` — adapters for Codex / GitHub Copilot.
- `reference/` (when the skill has enough volume to benefit from progressive disclosure).

## Skills

| Skill | What it does |
|-------|--------------|
| [`dump`](plugins/shnz/skills/dump/) | Generates focused code context bundles with `repomix` for use in third-party AI tools. Trigger: `/dump`, "context dump", "bundle for [tool]". |
| [`agent-browser`](plugins/shnz/skills/agent-browser/) | Drives any web UI with the `agent-browser` CLI and a persistent per-site registry (gitignored) that accumulates selectors, gotchas, and workflows across sessions. |
| [`narrative-commit`](plugins/shnz/skills/narrative-commit/) | Analyses uncommitted changes, groups them by layer/feature, proposes a conventional-commits plan, and (on approval) creates the commits. No AI attribution in messages. |

## Installing

Point Claude Code at this marketplace (adjust path if cloned elsewhere):

```
/plugin add /Users/one/Projects/SteveHoggNZ/skills
```

Skills are invoked via natural language matching their `description`, or explicitly via `/<skill-name>` when they register a slash command.

## Developing a skill

Before promoting a new skill — or a significant change — validate that it actually helps. The methodology is in [docs/AB_TESTING.md](docs/AB_TESTING.md). Running an A/B with two subagents is cheap and surfaces wrong assumptions quickly (the first A/B on `agent-browser` caught two incorrect selector claims its own registry had recorded).

## Conventions

- Skills are multi-agent where it's cheap to be: a `core.md` + thin adapter files.
- Anything the skill learns at runtime (e.g. `agent-browser`'s `.registry/`) is gitignored per-skill. Shared knowledge lives in the committed reference material.
- Skill directories are self-contained — no cross-skill imports.
