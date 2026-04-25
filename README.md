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
│       ├── hooks/                            # plugin-level lifecycle hook contracts
│       │   └── on_session_end.md             # onSessionEnd hook (registered skills, contract, registration pattern)
│       ├── agents/                           # plugin-scoped orchestrators spanning multiple skills (reserved)
│       │   └── README.md
│       └── skills/
│           ├── dump/                         # repomix-based context bundling
│           ├── agent-browser/                # browser automation CLI + per-site registry
│           ├── narrative-commit/             # split uncommitted changes into a clean conventional-commits sequence
│           ├── docker-roast/                 # opinionated Dockerfile linter wrapper (droast) with demo examples
│           ├── create-concept-website/       # scaffold a zero-build single-page HTML concept site (Vision/Roadmap/Map) with slide mode + PDF export
│           ├── inspect-session/              # parse a session JSONL and report tokens, cost, turns, tool calls, latency
│           ├── ui-state-debugging/           # pattern skill: methodology for diagnosing client/server state-discrepancy bugs
│           ├── ui-render-stability/          # pattern skill: ffmpeg frame analysis + anti-pattern catalogue for UI flash, CLS, mount-thrash
│           └── skill-iterate/                # meta-skill: iterate a target skill toward convergence
└── docs/                                     # cross-cutting process notes
    ├── AB_TESTING.md                         # how to validate that a skill actually helps
    ├── COMPOSITION.md                        # pattern vs procedure skills, how repo-local skills draw on global ones, the resource matrix
    └── INSTALL.md                            # full install / update / uninstall flows
```

**On the symlinks.** The canonical manifests live in `.claude-plugin/` because that path is read natively by both Claude Code and GitHub Copilot CLI. The symlinks at `/marketplace.json`, `.github/plugin/marketplace.json`, and `plugins/shnz/plugin.json` point at the canonicals so every supported client — and human browsers on the repo — finds the same file. Edit the canonical; the symlinks follow automatically.

*Windows note:* Git needs `core.symlinks=true` (the default on modern Git for Windows with Developer Mode enabled) to materialise symlinks on checkout. Without it, the symlinked files clone as plain text containing the target path.

Each skill directory follows the same layout:

- `SKILL.md` — Claude Code entry point (frontmatter + pointer to `core.md`).
- `core.md` — canonical, agent-agnostic procedure.
- `AGENTS.md` / `copilot-instructions.md` — adapters for Codex / GitHub Copilot.
- `reference/` (when the skill has enough volume to benefit from progressive disclosure).

Plugin-level directories sit above skills:

- `hooks/` — lifecycle hook contracts. Each file documents one hook event, lists which skills register for it, and gives the registration pattern.
- `agents/` — reserved for plugin-scoped orchestrators that coordinate multiple skills. Individual skill sub-agents stay inside their skill directory.

## Skills

| Skill | What it does |
|-------|--------------|
| [`dump`](plugins/shnz/skills/dump/) | Generates focused code context bundles with `repomix` for use in third-party AI tools. Trigger: `/dump`, "context dump", "bundle for [tool]". |
| [`agent-browser`](plugins/shnz/skills/agent-browser/) | Drives any web UI with the `agent-browser` CLI and a persistent per-site registry (gitignored) that accumulates selectors, gotchas, and workflows across sessions. |
| [`narrative-commit`](plugins/shnz/skills/narrative-commit/) | Analyses uncommitted changes, groups them by layer/feature, proposes a conventional-commits plan, and (on approval) creates the commits. No AI attribution in messages. |
| [`docker-roast`](plugins/shnz/skills/docker-roast/) | Wraps the opinionated [`droast`](https://github.com/immanuwell/dockerfile-roast) Dockerfile linter (63 rules, humorous commentary). Prefers a local binary, falls back to the official Docker image — zero install required. Ships 3 deliberately-bad + 1 reference-good demo Dockerfiles via the `examples` subcommand. |
| [`create-concept-website`](plugins/shnz/skills/create-concept-website/) | Scaffolds a **zero-build, single-page HTML** concept website that explains a concept top-down (Vision = why / art of the possible) and bottom-up (Roadmap = tactical waves; Map = the layers with readiness levels). One `index.html` + `assets/style.css` + `assets/script.js` — opens directly from `file://`, no Jekyll, no Node. Designed to get a group of people on the same page. Modeled on [stevehoggnz.github.io/ai-sdlc](https://stevehoggnz.github.io/ai-sdlc/). Includes slide-deck present mode (arrow-key nav, no content duplication) and PDF export (print CSS baseline + optional Puppeteer build script). Trigger: `/create-concept-website`, "concept website for X", "vision + roadmap site". |
| [`inspect-session`](plugins/shnz/skills/inspect-session/) | Parses a Claude Code session JSONL and reports **start/end, duration, user/assistant turns, tool-call breakdown, slash commands, tokens by bucket (input/output/cache-read/cache-creation 5m+1h), cache hit rate, USD cost with per-bucket breakdown, cost per user turn, and assistant-turn latency (min/median/p90/max)**. Defaults to the most recent session in the current project; accepts a session UUID or explicit `.jsonl` path. Markdown by default; `--json` for pipes. Stdlib-only Python, zero install. Trigger: `/inspect-session`, "session metrics", "how much did this cost". |
| [`ui-state-debugging`](plugins/shnz/skills/ui-state-debugging/) | **Pattern skill.** Methodology + reference catalogue for diagnosing client/server state-discrepancy bugs (bubbles stuck spinning, indicators that won't clear, UI showing different data than the database). Provides the three-layer verification model (DB → API → cache → render), positive-evidence design principle, instrumentation patterns, and known anti-patterns (negative-evidence cache seeds, client-side ghost-busters, snapshot races, HMR-context-stalls). Pairs with [`agent-browser`](plugins/shnz/skills/agent-browser/) (tool) and a repo-local skill (codebase-specific recipes). Auto-loads when the user describes "stuck", "won't clear", "still showing X", "wrong status", or a screenshot disagrees with what you can see live. |
| [`ui-render-stability`](plugins/shnz/skills/ui-render-stability/) | **Pattern skill.** Methodology + reference catalogue for diagnosing visual instability — flashing during navigation, layout shift (CLS), chrome that mounts/unmounts, content swaps without skeleton states, transition jank. Unique technique: ffmpeg-driven video frame analysis (scene detection at transitions, before/after PNG extraction, side-by-side comparison) — turn a 5-second screen recording into a structured timeline of what changed when. Anti-pattern catalogue covers conditional layout chrome, skeleton-state conflation, CLS sources, cache invalidation cascades, and mount/unmount thrash. Maintains a per-origin registry of app-specific conditional-chrome quirks. Auto-loads when the user describes "flashes", "flickers", "jumps", "snaps in", "janky", or provides a video showing visual discontinuity. |
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

For deciding whether a new skill should exist at all — and how it should compose with skills you already have — see [docs/COMPOSITION.md](docs/COMPOSITION.md). It distinguishes **pattern skills** (catalogues of methodology and gotchas, e.g. `ui-state-debugging`) from **procedure skills** (end-to-end workflows, e.g. `narrative-commit`), explains how repo-local skills draw on global ones without explicit imports, and gives the resource matrix for *where* learned artifacts should live (in the skill, in the repo, or in a per-site registry).

## Conventions

- Skills are multi-agent where it's cheap to be: a `core.md` + thin adapter files.
- Anything the skill learns at runtime (e.g. `agent-browser`'s `.registry/`) is gitignored per-skill. Shared knowledge lives in the committed reference material.
- Skill directories are self-contained — no cross-skill imports. Plugin-level `hooks/` and `agents/` directories are the intentional exception: they coordinate across skills at the plugin boundary.
- Pattern skills and procedure skills compose at runtime via the consuming agent, not via mutual references. See [docs/COMPOSITION.md](docs/COMPOSITION.md) for the full pattern.
