# Rule catalog and skip guidance

`droast` ships with 63 rules. Run `droast --list-rules` for the authoritative current list; this file is the agent-facing cheat sheet for interpreting findings and deciding which rules are safe to skip in which contexts.

## Rule themes

| Theme | Sample rules | What they protect |
|---|---|---|
| **Safety** | DF002, DF010, DF013, DF014, DF020, DF021, DF034 | Container runs as non-root, no secrets baked in, no `wget \| sh`, sensible permissions |
| **Reproducibility** | DF001, DF005, DF024, DF028 | Pinned tags and versions, cache-bust `apt-get update` |
| **Image size / layers** | DF003, DF004, DF007, DF011, DF026, DF029, DF033 | Combine RUN, clean caches in-layer, multi-stage, respect `.dockerignore` |
| **Correctness** | DF025, DF036, DF038, DF039, DF040, DF041, DF042, DF048, DF049, DF050 | JSON-array exec form, don't duplicate CMD/ENTRYPOINT/HEALTHCHECK, valid port range, multi-stage stage references |
| **Ecosystem hygiene** | DF015/16 (apt), DF027 (yum), DF029 (apk), DF030 (pip), DF031 (npm), DF032 (Python env), DF043–47 (zypper/dnf/yum cache) | Package manager best practices per ecosystem |
| **Interface** | DF017, DF018, DF022, DF037 | `ENTRYPOINT + CMD` shape, documented `EXPOSE`, valid opening instruction |

## High-signal rules (rarely worth skipping)

These catch real production pain. Push back if the user wants to skip them.

- **DF002 / DF020** — no explicit non-root USER. Running as root in a container is a genuine security issue; skipping this should require a concrete reason.
- **DF013 / DF014** — secrets in ENV / hardcoded tokens. Build-time leak.
- **DF001 / DF024** — `:latest` base images. Reproducibility incident waiting to happen.
- **DF028** — apt-get update not cache-busted. Works locally, mysteriously bakes stale packages on rebuild.
- **DF034** — `chmod 777`. Flag for review every time.
- **DF021** — `wget | sh`. Supply-chain risk.

## Rules that sometimes deserve `--skip`

These are context-sensitive. Flag to the user when they fire, let them decide.

- **DF011** (multi-stage builds) — not every image benefits. Tiny CLI tools / single-binary images can reasonably skip this.
- **DF012** (HEALTHCHECK) — irrelevant for short-lived jobs / CI images / one-shot CLI containers.
- **DF017** (ENTRYPOINT + CMD) — opinionated. Some projects intentionally use only CMD.
- **DF022** (EXPOSE) — purely documentary; some teams view it as noise.
- **DF005** (pinned package versions) — pinning everything is high-maintenance. Many teams pin only production dependencies.
- **DF032** (PYTHONDONTWRITEBYTECODE / PYTHONUNBUFFERED) — irrelevant for non-Python images (`droast` only fires it when it detects Python, but if the detection is wrong, skip).

## Rules that depend on project convention

When these fire, surface them to the user and defer to project policy — there's no universal right answer.

- **DF003** (combine RUN) — strict combining hurts readability; modern BuildKit caching partly mitigates the size concern.
- **DF025** (JSON array CMD/ENTRYPOINT) — shell form is sometimes intentional for env-var expansion.
- **DF007** (COPY . .) — bad for cache invalidation but convenient for tiny projects.

## How to present findings to the user

1. **Keep the roast commentary by default.** The tone IS the product. Only strip with `--no-roast` when the user asks for terse output.
2. **Group by severity**, errors first. Within a severity, optionally group by rule when a single rule fires on many lines ("DF001 fires on 3 base-image lines").
3. **Cite line numbers verbatim** from `droast`'s output. Don't paraphrase.
4. **Suggest fixes, don't apply them.** A fix for one rule may conflict with the user's intent for another rule; the human decides.

## Applying a fix

When the user approves a fix:

- Use `Edit` (or your host's equivalent) with a precise `old_string` / `new_string`. Do NOT rewrite the whole Dockerfile.
- Re-run `droast` after the fix to confirm the finding cleared AND that no new findings appeared.
- If the fix reveals a dependent finding (e.g. fixing DF001 to pin a tag then reveals DF005 about package versions), surface it — don't silently expand scope.

## Structured output

For CI-style parsing, use `--format json`. Each finding includes `rule_id`, `severity`, `line`, `message`, and `roast`. Use JSON when you need to:

- Count findings per rule for a summary.
- Decide programmatically whether a build should fail (see `--no-fail` inverse).
- Diff findings across a before/after comparison when verifying a fix.
