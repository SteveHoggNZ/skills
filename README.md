# shnz-skills

Vendor-neutral skill marketplace for agentic automation — a small, opinionated collection of skills that work with any SKILL.md-compatible client. Tested with Claude Code and GitHub Copilot CLI.

## Structure

```
/
├── marketplace.json                          # → .claude-plugin/marketplace.json (symlink, for humans)
├── .claude-plugin/
│   └── marketplace.json                      # canonical marketplace manifest
├── .github/
│   └── plugin/
│       └── marketplace.json                  # → ../../.claude-plugin/marketplace.json (symlink, Copilot's preferred path)
├── plugins/
│   └── shnz/                                 # the plugin bundling all skills in this repo
│       ├── plugin.json                       # → .claude-plugin/plugin.json (symlink, Copilot-friendly plugin-root path)
│       ├── .claude-plugin/
│       │   └── plugin.json                   # canonical plugin manifest
│       └── skills/
│           ├── dump/                         # repomix-based context bundling
│           ├── agent-browser/                # browser automation CLI + per-site registry
│           ├── narrative-commit/             # split uncommitted changes into a clean conventional-commits sequence
│           ├── docker-roast/                 # opinionated Dockerfile linter wrapper (droast) with demo examples
│           ├── create-concept-website/       # scaffold a zero-build single-page HTML concept site (Vision/Roadmap/Map) with slide mode + PDF export
│           └── skill-iterate/                # meta-skill: iterate a target skill toward convergence
└── docs/                                     # cross-cutting process notes
    ├── AB_TESTING.md                         # how to validate that a skill actually helps
    └── INSTALL.md                            # full install / update / uninstall flows
```

**On the symlinks.** The canonical manifests live in `.claude-plugin/` because that path is read natively by both Claude Code and GitHub Copilot CLI. The symlinks at `/marketplace.json`, `.github/plugin/marketplace.json`, and `plugins/shnz/plugin.json` point at the canonicals so every supported client — and human browsers on the repo — finds the same file. Edit the canonical; the symlinks follow automatically.

*Windows note:* Git needs `core.symlinks=true` (the default on modern Git for Windows with Developer Mode enabled) to materialise symlinks on checkout. Without it, the symlinked files clone as plain text containing the target path.

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
| [`docker-roast`](plugins/shnz/skills/docker-roast/) | Wraps the opinionated [`droast`](https://github.com/immanuwell/dockerfile-roast) Dockerfile linter (63 rules, humorous commentary). Prefers a local binary, falls back to the official Docker image — zero install required. Ships 3 deliberately-bad + 1 reference-good demo Dockerfiles via the `examples` subcommand. |
| [`create-concept-website`](plugins/shnz/skills/create-concept-website/) | Scaffolds a **zero-build, single-page HTML** concept website that explains a concept top-down (Vision = why / art of the possible) and bottom-up (Roadmap = tactical waves; Map = the layers with readiness levels). One `index.html` + `assets/style.css` + `assets/script.js` — opens directly from `file://`, no Jekyll, no Node. Designed to get a group of people on the same page. Modeled on [stevehoggnz.github.io/ai-sdlc](https://stevehoggnz.github.io/ai-sdlc/). Includes slide-deck present mode (arrow-key nav, no content duplication) and PDF export (print CSS baseline + optional Puppeteer build script). Trigger: `/create-concept-website`, "concept website for X", "vision + roadmap site". |
| [`skill-iterate`](plugins/shnz/skills/skill-iterate/) | **Meta-skill.** Drives a target skill toward its optimal floor by running a probe subagent on a concrete task, collecting a structured report, applying concrete edits on your approval, and repeating until the probe reports no friction. Complements `docs/AB_TESTING.md` (A/B is "should this skill exist?"; `skill-iterate` is "is it as good as it can be?"). |

### Naming convention

Skills whose job is to operate on other skills use the **`skill-*` prefix** (currently: `skill-iterate`; possible future additions: `skill-review`, `skill-doctor`, `skill-scaffold`). Non-meta skills don't use the prefix. Reading a listing, you can tell meta-skills at a glance.

## Installing

See [docs/INSTALL.md](docs/INSTALL.md) for the full install + update + uninstall flow, including the developer mode for hacking on this marketplace.

**TL;DR — as a consumer.**

In a Claude Code session:

```
/plugin marketplace add SteveHoggNZ/skills
/plugin install shnz@shnz-skills
```

Or in GitHub Copilot CLI:

```
copilot plugin marketplace add SteveHoggNZ/skills
copilot plugin install shnz
```

Either client clones the repo into its own managed cache and picks up updates on startup. This repo is **private** — collaborator access with SSH loaded (`ssh-add`) or a host-appropriate token (`GITHUB_TOKEN` for both clients) is required for background auto-updates. Pin to a version with `SteveHoggNZ/skills@v1.0` if you want a specific tag/branch/commit.

Skills are then invoked via natural language matching their `description`, or explicitly via `/<skill-name>` when they register a slash command. Developers editing this marketplace should install from a local clone instead — see [INSTALL.md](docs/INSTALL.md#for-developers).

## Developing a skill

Before promoting a new skill — or a significant change — validate that it actually helps. The methodology is in [docs/AB_TESTING.md](docs/AB_TESTING.md). Running an A/B with two subagents is cheap and surfaces wrong assumptions quickly (the first A/B on `agent-browser` caught two incorrect selector claims its own registry had recorded).

## Conventions

- Skills are multi-agent where it's cheap to be: a `core.md` + thin adapter files.
- Anything the skill learns at runtime (e.g. `agent-browser`'s `.registry/`) is gitignored per-skill. Shared knowledge lives in the committed reference material.
- Skill directories are self-contained — no cross-skill imports.
