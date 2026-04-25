---
name: docker-roast
kind: procedure
description: "Lint a Dockerfile with the opinionated 63-rule linter `droast` (dockerfile-roast). Use when the user says 'lint my Dockerfile', 'roast my Dockerfile', 'review Dockerfile', 'check Dockerfile best practices', 'find Dockerfile issues', or invokes /docker-roast. Supports subcommands: default run against Dockerfile(s), 'examples' to install bundled demo Dockerfiles, 'install' to set up droast locally, 'help' for usage. Prefers a local droast binary; falls back to the ghcr.io/immanuwell/droast Docker image so no install is required."
argument-hint: "[path-or-glob | examples [dest] | install | help]"
---

<!-- Claude Code adapter — canonical procedure in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Claude Code specifics

- **Parse `ARGUMENTS` to dispatch subcommands** (see core.md §"Subcommand dispatch"). Empty args → default run; `examples`/`install`/`help` → named subcommand; anything else → treat as target path.
- **Detect the runner once** (local `droast` → Docker image → neither) and reuse. Use `Bash` with a single detection call at the start.
- **Use dedicated tools**:
  - `Bash` — runner detection, running droast, copying example files (`cp`), install commands.
  - `Read` — inspecting target Dockerfiles + bundled examples when the user wants explanation.
  - `Edit` — applying approved fixes surgically (never rewrite whole Dockerfiles).
  - `Glob` — finding Dockerfiles in CWD when no path is provided.
- **Bundled examples live at** `<skill-dir>/examples/*.Dockerfile` — 3 deliberately-bad + 1 reference-good. Each file's header comment lists the rules it's designed to trigger.
- **Never apply fixes or install commands without explicit user approval.** The point of `droast` is surfacing opinions; the user decides which to act on.
- **Keep the roast commentary by default.** Only strip with `--no-roast` when the user asks for terse output.

## Runner selection (summary)

1. `command -v droast` → use the local binary (fastest).
2. Else `command -v docker` → use `docker run --rm -v <dir>:/work -w /work ghcr.io/immanuwell/droast <args>`.
3. Else → advise `/docker-roast install` and stop.

## Typical first interaction

1. User says "lint my Dockerfile" or `/docker-roast`.
2. Detect runner, resolve targets (CWD glob if not specified).
3. Run with `--format compact` for human output (or `--format json` when you need to programmatically act on findings).
4. Report findings grouped by severity, keeping the roast commentary.
5. Offer follow-ups: fix specific findings, skip specific rules, or explain a rule.