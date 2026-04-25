# Skill composition

How skills compose with each other, how repo-local skills draw on global ones, and where the artifacts they produce should live.

## The two flavours of skill

A skill in this marketplace is one of two shapes. Knowing which you're writing — and which you're consuming — is most of the design work.

### Procedure skills (prescriptive)

A procedure skill says: *"to do X, follow these steps."* It owns a workflow end-to-end. The agent reads it and then executes the steps largely as written.

Examples in this marketplace:

- [`narrative-commit`](../plugins/shnz/skills/narrative-commit/) — "to commit a pile of mixed changes, group → propose → approve → stage → commit."
- [`agent-browser`](../plugins/shnz/skills/agent-browser/) — "to drive a website, load the registry → run commands → update the registry."
- [`inspect-session`](../plugins/shnz/skills/inspect-session/) — "to report on a session, parse the JSONL → format the metrics → print."

Procedure skills tend to be invoked via slash command or a clear trigger phrase. The user is asking *for the procedure*.

### Pattern skills (descriptive)

A pattern skill says: *"here are the patterns and gotchas in this domain — compose your own approach from them."* It is a library, not a script.

Examples (current and possible):

- [`ui-state-debugging`](../plugins/shnz/skills/ui-state-debugging/) — three-layer verification, instrumentation patterns, positive-evidence design. The agent picks the relevant patterns; there is no single linear procedure.
- A future `react-performance-debug` skill would be the same shape: a catalogue of techniques (profiling, memo audit, suspense waterfalls), not a 10-step script.

Pattern skills tend to be invoked when the agent recognises the domain ("this is a UI state-discrepancy bug — load the patterns") rather than via a literal trigger phrase. The agent is asking the skill *for vocabulary and recipes*, not for a script.

**Why distinguish.** A pattern skill written in a procedural tone forces the agent down one path when the bug needs a different one. A procedure skill written as scattered patterns leaves the agent freelancing. Get the shape wrong and the skill underperforms even when its content is right.

## Skills drawing on skills

Skills don't `import` each other (that's an explicit non-goal — every skill is self-contained). But they *do* compose at runtime: the agent loads multiple skills in the same session and combines their procedures.

Two composition patterns are common:

### Pattern + Procedure: methodology + tool

A pattern skill provides the *methodology*; a procedure skill provides the *tool*. The agent uses both together.

Worked example:

> User: "The bubble is stuck spinning even though the agent finished. Figure out why."
>
> Agent loads:
> - `ui-state-debugging` — pattern skill, gives the three-layer verification methodology
> - `agent-browser` — procedure skill, gives the browser-driving recipe
>
> Agent applies the methodology (check DB, check API, check client cache) and uses the tool to inspect the client cache step.

Neither skill knows about the other. The composition lives in the agent's reasoning. **This is the right level of coupling** — tighter and you'd have hidden dependencies; looser and the agent wouldn't know they fit together.

### Repo-local + global: specific + generic

A repo-local skill (in `<repo>/.claude/skills/`) is allowed to assume a global skill is loaded and reference its concepts. It scopes the global patterns to the specific codebase.

Worked example:

> `amp-stream-bubble-diagnostics` (repo-local) references the three-layer verification pattern from `ui-state-debugging` (global) and provides the AMP-specific commands for each layer:
> - Layer 1 (DB): "query `public.message_streams WHERE channel_id = … AND closed_at IS NULL`"
> - Layer 2 (API): "curl `/api/v2/channels/{id}/entries` and check `closed_streams[]`"
> - Layer 3 (client): "navigate via agent-browser, dump `window.__streamStatusMap`"

The generic skill defines the concept; the local skill provides the codebase-specific recipes. Reading them together gives you both vocabulary and concrete steps. Reading either alone is incomplete.

**This is the inheritance-like pattern** the user asked about. Not class inheritance — a global skill can't `extend` a repo-local one because it doesn't know it exists. But the *consumer* (the agent) treats the repo-local skill as specialising the global one for this codebase.

## The resource matrix

When a skill produces an artifact (a script, a finding, a fingerprint), where does it live? Route by **who needs it next** and **what it's coupled to**.

| Artifact type                              | Lives in                                              | Why                                                                                |
|--------------------------------------------|-------------------------------------------------------|------------------------------------------------------------------------------------|
| Codebase-specific tooling (test rigs, fixtures, repro scripts) | The target repo (`<repo>/scripts/`, committed)         | Coupled to the schema/UI/business logic. A future refactor must update it in the same PR. |
| Per-site or per-app fingerprints (selectors, gotchas, login flow) | The relevant procedure skill's `.registry/<slug>.md`, gitignored, keyed by URL origin | The same site is the same site regardless of which repo I'm cd'd into. Cross-repo continuity matters. |
| Methodology / generic patterns (debugging frameworks, design principles) | A global pattern skill in this marketplace           | Applies to any project of the relevant shape. Don't trap it in one repo's skills/. |
| Codebase-specific recipes (file paths, commands, architectural rules) | A repo-local skill in `<repo>/.claude/skills/`        | Tied to this repo's conventions. Ship with the code so it stays in sync.            |
| Framework gotchas (Vite quirks, Playwright behaviour) | The relevant procedure skill's reference material, NOT a separate "gotchas" file | Find them where you'll be looking when they bite you (in the tool's docs).         |

Two anti-patterns this matrix prevents:

- **Trap-the-knowledge-in-the-repo.** Codifying methodology inside `<repo>/.claude/skills/` means a different repo with the same problem class has to rediscover it.
- **Forced-template sprawl.** Inventing a "test rig builder" skill whose value is "saves you 30 lines of Playwright boilerplate" — the agent diverges from the template on the first real customisation, and you've added a skill to maintain for negative value.

## Self-improvement loops

A skill that doesn't update itself decays. Every skill in this marketplace that accumulates runtime knowledge follows the same loop, codified at the bottom of its `core.md`:

> **At the end of every task**: if you learned anything non-obvious, update (or create) the relevant artifact. Bump `last_updated`. Don't be a packrat — only record what would save a future agent time.

Where "the relevant artifact" lives depends on the kind of learning:

- **Site-specific**: `<skill>/.registry/<origin>.md` (gitignored within the skill).
- **Codebase-specific**: a repo-local skill's reference file, or the repo's runbooks.
- **Generic / framework-level**: the global skill's `reference/*.md`, committed.

Two design principles for the loop to actually pay off:

1. **Be specific about what's worth recording.** "Surprises and speed-ups; not UI inventories." The intent reminder in `agent-browser`'s registry frontmatter is the canonical phrasing. Without this, the registry fills with low-value detail and future agents stop reading it.
2. **The artifact is agent-facing, not human-facing.** It exists to let the next agent skip relearning, not to be read like a manual. This justifies the terse style and the deletion of stale entries.

## When to create a new skill vs extend an existing one

Sprawl is the failure mode. Default to extending.

Create a new skill when:

- A new domain emerges that the agent will recognise on its own (e.g. "this is a database migration task" → load a `database-migrations` skill). The skill earns its keep by being loadable on demand without being mentioned by name.
- The split makes the existing skill cleaner — e.g. a procedure skill grew an entire methodology section that was crowding out the procedure.
- The audience differs — a global pattern skill should not contain a single repo-local file path, even if extracting them feels heavy.

Extend an existing skill when:

- The new content is "more of the same kind of thing" — another command in `agent-browser/reference/commands.md`, another gotcha in `agent-browser/reference/gotchas.md`.
- The new content is methodology that fits inside a procedure skill's "principles" section.
- You're tempted to create a "sister skill" that would always be loaded alongside the existing one — fold it in instead.

### Special case: repo-local diagnostic skills

Repo-local diagnostic skills (e.g. `amp-stream-bubble-diagnostics`) should be **one per coherent architectural domain**, not catch-alls. **Granularity tracks the architecture, not the prefix.**

The temptation is to create one broad `<repo>-diagnostics` skill that covers "everything debug-related in this codebase." Don't. The agent's tool picker matches against the `description` field; a broad description forces the skill to load on far too many tasks, burning context on irrelevant reference material. Narrow skills with focused descriptions are *cheaper* — the picker does the routing for free.

When two diagnostic skills would share no files, no DB tables, and no architectural invariants, they're separate domains. Create siblings (`<repo>-stream-bubble-diagnostics`, `<repo>-frame-diagnostics`, `<repo>-workflow-diagnostics`); don't conflate them. For human discoverability across the siblings, write a `<repo>/.ai/runbooks/diagnostics-index.md` that maps symptoms to skills — that's documentation, not a skill, and it costs the agent nothing.

## Naming and frontmatter conventions

The shape of a skill — pattern, procedure, or meta — is signalled **twice**: in the name (for humans skimming a listing) and in the `kind:` frontmatter field (for tooling that wants a machine-readable filter). Redundancy aids comprehension when one channel is missed.

### `kind:` frontmatter

Every `SKILL.md` declares its kind explicitly:

```yaml
---
name: <skill-name>
kind: procedure | pattern | meta
description: "..."
---
```

Tooling that renders the marketplace listing (or `/help`, or skill search) can group / filter by `kind`. The values are exhaustive — every skill must be one of the three.

### Naming convention

| Kind | Naming shape | Examples |
|---|---|---|
| **Procedure** (action; user invokes it) | Verb-led or verb-final; reads as a command | `dump`, `inspect-session`, `create-concept-website`, `narrative-commit` |
| **Pattern** (knowledge body; agent consults it) | Noun phrase or gerund; reads as a domain | `ui-state-debugging`, hypothetical `react-performance`, hypothetical `database-migrations` |
| **Meta** (operates on other skills) | `skill-*` prefix | `skill-iterate`, hypothetical `skill-review`, hypothetical `skill-doctor` |

The grammatical mood does the work an underscore prefix would otherwise do — and more honestly, because pattern skills aren't *private* (the agent absolutely uses them), they're a different **invocation mode**: user-driven for procedure, symptom-recognition for pattern.

**Grandfathered exceptions:**
- `agent-browser` is a procedure skill named after the underlying CLI (also called `agent-browser`). Renaming would break muscle memory; the noun-phrase name is the cost. Document as the exception.

**Repo-local skills** live in `<repo>/.claude/skills/` and SHOULD prefix with the project name to make ownership obvious in mixed listings: `amp-ui-validate`, `amp-stream-bubble-diagnostics`. The procedure/pattern/meta classification still applies — repo-local pattern skills exist (codebase-specific debugging knowledge that's larger than a procedure but smaller than a global pattern).

## Per-origin registry pattern

Skills that accumulate **app-specific knowledge across sessions** use a per-origin registry: a directory of Markdown files inside the skill, keyed by URL origin, gitignored.

`agent-browser` introduced this pattern; `ui-state-debugging` reuses it. Both can coexist on the same origin — they capture different aspects:

- `agent-browser/.registry/<slug>.md` — "how to *drive* this site" (selectors, login flow, gotchas about UI behaviour)
- `ui-state-debugging/.registry/<slug>.md` — "how to *debug state issues on* this site" (false-positive bug shapes, framework debugging quirks, layer pointers)

### Registry rules (apply to any skill using the pattern)

- **Key**: URL origin (`scheme://host:port`), normalized to a slug (`localhost-4173.md`). Two distinct apps sharing one origin (dev-tunnel multiplexing) get a path discriminator suffix.
- **Storage**: `<skill>/.registry/<slug>.md`. Always inside the skill, never in the consuming repo (cross-repo continuity is the whole point).
- **Gitignored**: the `.registry/` directory is in the skill's `.gitignore`. The format / examples are committed in a `reference/registry-format.md`; the entries themselves are local-only.
- **Contents**: agent-facing hindsight, not human-facing documentation. Surprises and speed-ups; not UI inventories. The exact "what belongs / what doesn't" rules belong in the skill's own `registry-format.md`.
- **Lifecycle**: load at the start of every session for the matching origin (skip if none); update at the end if anything non-obvious was learned.

### When a skill should adopt the pattern

If the skill is invoked across distinct applications and **the same application is likely to be touched in multiple repos / sessions**, the pattern pays off. Otherwise the registry stays empty and adds noise.

Procedure skills like `narrative-commit` and `dump` don't benefit — their behaviour doesn't depend on knowing the target codebase intimately. They're per-invocation, not per-application.

## See also

- [AB_TESTING.md](./AB_TESTING.md) — validating that a new skill actually helps before promoting it. Especially important for pattern skills, where the "did this help?" question is harder than for procedure skills.
- [INSTALL.md](./INSTALL.md) — install / update / uninstall flow.
