# Docker Roast

Wrap the [`droast`](https://github.com/immanuwell/dockerfile-roast) Dockerfile linter as an opinionated code-review step. `droast` has 63 rules across safety (non-root USER, secrets, `chmod 777`), reproducibility (pinned tags, cache busting), size (multi-stage, layer combining), and correctness (mutually-exclusive instructions, invalid ports). This skill:

- Runs it against the target Dockerfile(s) with minimal friction (prefers a local `droast` binary, falls back to the official Docker image so no install is required).
- Parses the output and surfaces findings with context + suggested fixes.
- Ships bundled example Dockerfiles (3 deliberately-bad + 1 reference-good) so the skill is demonstrable with no user setup.
- Helps the user install `droast` locally if they'd prefer not to rely on the Docker image.

## Subcommand dispatch

The slash command is `/docker-roast [ARGUMENTS]`. Parse the first whitespace-separated token of `ARGUMENTS`:

| First token | Meaning |
|---|---|
| *(empty)* | Default run mode against Dockerfiles in the current working directory |
| `examples` | Copy bundled example Dockerfiles to a test directory |
| `install` | Guide the user through installing `droast` locally |
| `help` | Print the usage block |
| Anything else (looks like a path or glob) | Treat as the target file/glob and run default mode against it |

Remaining tokens are passed through to the dispatched flow as additional arguments.

## Runner detection

Detect which runner to use **once**, reuse for the rest of the invocation:

1. `command -v droast` — if present, run `droast` directly. Fastest startup, best if the user has it installed.
2. Else `command -v docker` — run via `docker run --rm -v <abs-dockerfile-dir>:/work -w /work ghcr.io/immanuwell/droast <args>`.
3. Else neither available — advise the user to run `/docker-roast install` and stop.

Store the detected runner in a local variable so every subsequent command uses the same one.

## Default run mode

### 1. Resolve targets

- If `ARGUMENTS` (after subcommand parsing) is a path or glob, use it verbatim.
- Else list Dockerfiles in CWD: `Dockerfile`, `*.Dockerfile`, `**/Dockerfile`.
  - If none found, print usage and suggest `/docker-roast examples` to try the skill.
  - If exactly one, proceed.
  - If multiple, list them and ask the user which to lint (or confirm "all of them").

### 2. Run droast

Invoke via the detected runner. Prefer the `--format compact` output for terminal display; use `--format json` when the user asks for structured output or you intend to parse findings for follow-up fixes.

Example invocation via Docker image (note: the Dockerfile must be mounted):

```bash
docker run --rm \
  -v "$(pwd)/Dockerfile":/Dockerfile:ro \
  ghcr.io/immanuwell/droast \
  --format compact \
  /Dockerfile
```

If the user has pinned a preferred `min-severity` or `skip` list in prior conversation, apply those flags.

### 3. Surface findings

Report:

- **Total counts** by severity (info / warning / error).
- **Per-finding breakdown**: rule ID, severity, line number, short description, and — if `droast`'s output included the roast — the opinionated commentary (it's part of the value of this tool; don't strip it unless the user asked for `--no-roast`).
- **Grouping**: if there are >10 findings, group by severity (errors first) and collapse repeat-rule findings ("DF001 fires on 3 lines").

### 4. Offer follow-up

After presenting findings, ask whether the user wants:

- **A patch** applied to the Dockerfile (list specific fixes; get approval per-fix or in-bulk).
- **A rule skipped** (`--skip DFxxx`) — useful when a rule doesn't fit the project; record the skip list in conversation.
- **An explanation** of a specific rule and the canonical fix pattern.

Do not apply fixes unilaterally. The whole point of `droast` is to surface opinions; the user may disagree.

## `examples` subcommand

Copy the 4 bundled Dockerfiles from `<skill-dir>/examples/` to a destination directory so the user can run `droast` against them immediately.

### Usage

```
/docker-roast examples             # copies to ./docker-roast-examples/
/docker-roast examples /tmp/demo   # copies to the given directory
```

### Procedure

1. Determine destination: the second token of `ARGUMENTS` if present, else `./docker-roast-examples/`.
2. If the destination already exists and is non-empty, ask the user before overwriting.
3. Copy all four files from `<skill-dir>/examples/*.Dockerfile` into the destination, preserving the filenames.
4. Print the destination path and a short "try it" summary with four example commands:
   - `/docker-roast <dest>/bad-basic.Dockerfile`
   - `/docker-roast <dest>/bad-apt.Dockerfile`
   - `/docker-roast <dest>/bad-python.Dockerfile`
   - `/docker-roast <dest>/good.Dockerfile` (for the contrast)

Each example file carries a header comment listing the rules it's designed to trigger so the user can anticipate findings.

## `install` subcommand

Guide the user through a local install. See [reference/install.md](./reference/install.md) for the option matrix. High-level flow:

1. Detect the user's OS via `uname -s` (Darwin / Linux / other).
2. Detect available package managers (`command -v brew`, `command -v cargo`, `command -v docker`).
3. Recommend the lightest path:
   - Mac + brew available → `brew tap` + `brew install`.
   - Any OS + cargo available → `cargo install dockerfile-roast`.
   - Any OS + docker available → tell the user they already have a working runner (this skill's default), no install needed; offer the one-liner wrapper.
   - Otherwise point at the GitHub releases page for prebuilt binaries.
4. If the user approves, execute the install commands via Bash (with their confirmation).

Never install unilaterally. `cargo install` in particular is slow and takes real CPU.

## `help` subcommand / usage

Print a concise usage block listing the subcommands and a one-line example for each. If `ARGUMENTS` is empty AND no Dockerfile is present in CWD, print this block instead of erroring.

## What NOT to do

- Do not auto-skip rules that the user hasn't explicitly opted out of. `droast`'s opinions are the point.
- Do not hide the roast commentary by default. If the user wants terse output, they can ask for `--no-roast`.
- Do not edit Dockerfiles without approval.
- Do not `cargo install` or `brew install` without an explicit go-ahead.
