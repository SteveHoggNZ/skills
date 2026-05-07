# Patterns

Reusable building blocks. These are generic — they assume nothing about any particular site. Site-specific flows (which selector is the Sign-in button, where credentials live) belong in the site registry.

## The session command file

The skill invokes the CLI through a **session-scoped command file**: one script under `/tmp`, picked at the start of the session, rewritten per step, run directly with `bash`. No wrapper, no runner script — the command file is the thing you run.

**Properties:**

- **One approval per session** — every call is `bash <session-cmd-path>`, byte-identical across all steps in the session. Claude-Code-style exact-command approvals match once; the rest run silently.
- **No intra-session race** — tool calls within one session are sequential, so rewriting one shared file inside a session is safe.
- **No cross-session race** — two sessions starting concurrently pick distinct random suffixes, so their command files can't collide.

### Session setup (once, at the start of the session)

Pick ONE unique command-file path:

```
/tmp/ab-cmd-<YYYYmmddHHMMSS>-<4-char-random>.sh
```

- Use the current time to the second plus 4 random hex chars. The random component ensures two sessions starting in the same second still pick different paths.
- Record the path in your internal notes and do not change it for the rest of the session.

Example: `/tmp/ab-cmd-20260417-3f9a.sh`.

### Per invocation

1. Overwrite the session's command file — a normal shell script with shebang, `set -euo pipefail`, and the `npx agent-browser` call(s). Chain multi-steps with `&&`.
2. Run: `bash <session-cmd-path>`.
3. Repeat. The command file gets rewritten; the invocation string stays identical.

Always use absolute paths for any file outputs (screenshots, videos) inside the commands. The daemon's CWD may differ from the agent's. Cleanup is optional — `/tmp` is system-cleaned, and keeping the latest file around can help debug a failing chain.

### Example command files

**Snapshot only** — `/tmp/ab-cmd-20260417-3f9a.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
npx --yes agent-browser snapshot --interactive
```

**Click-then-snapshot chain**:

```bash
#!/usr/bin/env bash
set -euo pipefail
npx --yes agent-browser click @e13 \
  && npx --yes agent-browser wait 800 \
  && npx --yes agent-browser snapshot --interactive
```

**JS eval with captured result**:

```bash
#!/usr/bin/env bash
set -euo pipefail
npx --yes agent-browser eval "document.title"
```

### Permission setup

On the first invocation per session the host will prompt. Approving "always allow" covers the rest of the session, since the command string is identical.

To skip the once-per-session prompt, add a wildcard allow rule. For Claude Code (`~/.claude/settings.json`):

```json
{
  "permissions": {
    "allow": ["Bash(bash /tmp/ab-cmd-:*)"]
  }
}
```

(Adjust for other hosts' permission config. The principle is the same: match on the `/tmp/ab-cmd-` prefix.)

## Opening a new session

```bash
npx agent-browser open <url> --headed
npx agent-browser set viewport 1280 1024   # default viewport is often too small
npx agent-browser snapshot --interactive
```

If a registry entry recorded a working viewport, use that instead of 1280×1024.

## Login flow (generic shape)

```bash
# 1. Open and snapshot to find the Sign-in entry point.
npx agent-browser snapshot --interactive | grep -i "sign in\|log in\|login"

# 2. Click into the form.
npx agent-browser click @<sign-in-ref>

# 3. Re-snapshot — form refs didn't exist until now.
npx agent-browser snapshot --interactive

# 4. Fill and submit.
npx agent-browser fill @<email-ref> "<email>"
npx agent-browser fill @<password-ref> "<password>"
npx agent-browser click @<submit-ref>
npx agent-browser wait 2000
```

**Where do credentials come from?** Never hardcode them in the skill or registry. Point to the source in the registry entry (e.g. "credentials in project's `.env.users`" or "use 1Password item 'foo'"). The user or calling agent supplies them at runtime.

## Filling a standard form

```bash
npx agent-browser snapshot --interactive
npx agent-browser fill @<field1> "value1"
npx agent-browser fill @<field2> "value2"
npx agent-browser click @<submit>
```

For `contenteditable` fields see the clear-and-type recipe below.

## Clearing and typing into a rich-text editor

```bash
npx agent-browser eval "document.querySelector('[contenteditable=true]').innerHTML = '<p></p>'"
npx agent-browser click @<ref>
npx agent-browser type @<ref> "new content"
```

If the editor exposes a library API (TipTap, Monaco), calling that via `eval` is more robust:

```bash
# TipTap example (if the editor instance is exposed on window)
npx agent-browser eval "window.editor?.commands.setContent('')"
```

## Submitting when Enter doesn't work

If Enter creates a newline, locate and click the Submit/Send button:

```bash
npx agent-browser type @<input> "message body"
npx agent-browser snapshot --interactive | grep -iE "send|submit"
npx agent-browser click @<send-ref>
```

Record the site's Send-button selector in the registry so next session doesn't need the grep step.

## Waiting for something to happen

Prefer time-based waits for unknown territory; prefer selector-based waits when the selector is well-known and expected to exist. Avoid selector-based waits on uncertain matches (they hang for ~2.5 minutes).

```bash
# Time-based
npx agent-browser wait 1500

# Selector-based — only with a known-good selector
npx agent-browser wait "button[aria-label='Send']"

# Polling (safer when the selector is uncertain)
for i in 1 2 3 4 5; do
  npx agent-browser wait 500
  if npx agent-browser get count ".my-target" 2>/dev/null | grep -q "^[1-9]"; then break; fi
done
```

## Discovering an element without a stable selector

Start with `--interactive` and text grep:

```bash
npx agent-browser snapshot --interactive | grep -i "create channel"
```

If the text is non-unique, fall back to full snapshot with more context:

```bash
npx agent-browser snapshot | grep -B2 -A2 "Create"
```

Once you find a reliable way to identify the element (CSS selector, a11y label path), record it.

## Chaining for speed

Every CLI call is a daemon round-trip plus shell startup. Chain related steps:

```bash
npx agent-browser click @e13 \
  && npx agent-browser wait 800 \
  && npx agent-browser snapshot --interactive
```

Typical chain: click + wait + snapshot ≈ 0.8s end-to-end.

## Taking a screenshot

```bash
npx agent-browser screenshot /tmp/step-1.png
```

Use absolute paths — the daemon's CWD is not yours. Put screenshots under `/tmp/` unless the user has asked for a specific location.

## Recording a video

```bash
npx agent-browser record start /tmp/flow.webm
# ... run the flow ...
npx agent-browser record stop
```

**Keep recordings short — use a progressive duration strategy:**

1. **Start at 30 seconds.** Trigger the flow, wait 30s, stop, extract frames, check if the target event was captured.
2. **If not captured, retry at 60 seconds.** Re-run the flow with a 60s recording window.
3. **Then 90 seconds if still not captured.**
4. **Hard cap: 120 seconds.** Never record longer than 2 minutes — if the event hasn't occurred by then, the problem is not timing and recording further won't help. Stop and investigate the root cause instead.

Use `sleep` to enforce the window before stopping:
```bash
npx agent-browser record start /tmp/flow.webm
# ... trigger the flow ...
sleep 30 && npx agent-browser record stop
```

### Extracting frames for analysis

Scale down to **25% of the original resolution** (`scale=iw*0.25:-2`) to keep file sizes small. For animation or timing bugs where sub-second changes matter, use a higher fps — the original recording is often at 4fps or higher; the scale filter is what keeps it safe:

```bash
# Default: 4fps at 25% scale — good for animation/timing bugs
ffmpeg -i /tmp/flow.webm -vf "fps=4,scale=iw*0.25:-2" /tmp/frame-%04d.png

# Fewer frames for coarser state transitions (e.g. page loads, navigation):
ffmpeg -i /tmp/flow.webm -vf "fps=1,scale=iw*0.25:-2" /tmp/frame-%04d.png

# Very sparse — one frame every 2 seconds:
ffmpeg -i /tmp/flow.webm -vf "fps=1/2,scale=iw*0.25:-2" /tmp/frame-%04d.png
```

**Rules of thumb:**
- **Always include the scale filter** — full-resolution frames exceed the model's size limit (~1MB) and are silently dropped with "removed due to size constraints"
- Default to `fps=4,scale=iw*0.25:-2` — catches animation/timing bugs while staying well under size limits
- Drop to `fps=1` only when timing precision doesn't matter
- The original full-resolution 4fps extraction (no scale) was what caused the size issues — don't repeat that

## Reading page state with `eval`

Useful one-liners:

```bash
# Element exists?
npx agent-browser eval "!!document.querySelector('.foo')"

# Read text
npx agent-browser eval "document.querySelector('.title')?.textContent"

# Count matches
npx agent-browser get count "button"

# Active element
npx agent-browser eval "document.activeElement?.tagName"

# Document title
npx agent-browser eval "document.title"

# Current URL
npx agent-browser eval "location.href"
```

## React introspection (0.27+)

The `react *` subcommands need the React DevTools hook installed before the app mounts. **Open with `--enable react-devtools`** — bolting it on after navigation does not work.

```bash
# Daemon must be opened with the hook enabled. If a daemon is already running,
# `close` first; --enable is a launch-time flag.
npx agent-browser close
npx agent-browser open https://app.example.com --enable react-devtools
# react tree without --json silently emits "✓ Done" on 0.27.0 — always pass --json
npx agent-browser react tree --json | jq '.data.tree[] | "\(.id)\t\(.name)"' | head
npx agent-browser react inspect 47             # props, hooks, state, source, ancestor chain
```

### Profiling re-renders around an interaction

Wrap the interaction in `react renders start|stop`:

```bash
npx agent-browser react renders start
npx agent-browser click @e3
npx agent-browser wait 500
npx agent-browser react renders stop --json > /tmp/renders.json
```

The JSON output is the artifact to read — it lists which components re-rendered and how often. Pair with the `ui-render-stability` skill when the symptom is "this view feels janky".

### Suspense boundary classifier

Investigating a slow first paint or a flash that looks like a Suspense fallback?

```bash
npx agent-browser react suspense --only-dynamic --json
```

`--only-dynamic` filters out boundaries that never suspended in this session, which is almost always what you want.

## Web Vitals (0.27+)

```bash
npx agent-browser vitals --json
```

CLS and INP only accumulate values once the user (or the agent) interacts with or scrolls the page — call `vitals` *after* exercising the flow, not on the freshly-loaded idle page. When the build is a profiling React build, the report also includes hydration phase timings.

## SPA navigation without a full reload (0.27+)

`pushstate` triggers client-side navigation, preserving daemon state and avoiding a hard reload. Auto-detects Next.js (`window.next.router.push`) and falls back to `history.pushState` + `popstate`/`navigate` events.

```bash
npx agent-browser pushstate /dashboard
npx agent-browser wait 800
npx agent-browser snapshot --interactive
```

Prefer this over `open <new-url>` when testing **client routing** behavior (layout-chrome stability across route changes, RSC fetches, route-level Suspense). Use `open` for initial-load behavior.

## Reusing a real-browser session via cookie import (0.27+)

If you're already logged into the target site in your everyday browser, the fastest way to hand that session to the agent is `cookies set --curl <file>`. The flag is misnamed — it auto-detects three formats:

- **cURL** — paste the entire `curl '...' -H 'Cookie: ...'` line you copied from DevTools Network tab.
- **JSON** — what EditThisCookie / DevTools cookie-export emit.
- **Cookie-header** — a bare `Cookie: a=1; b=2` line. Requires `--domain <host>` to scope it.

```bash
# Copy as cURL from DevTools, save to /tmp/curl.sh, then:
npx agent-browser open https://app.example.com
npx agent-browser cookies set --curl /tmp/curl.sh
npx agent-browser open https://app.example.com    # now logged in
```

Don't commit the cookie file. For repeatable scripted login, use the auth vault instead.

## Network route filtering by resource type (0.27+, ⚠️ verify it fires)

`network route` accepts `--resource-type <csv>` (`image`, `font`, `script`, `xhr`, `fetch`, `media`, …). Useful when you want to stub only API calls without breaking page assets, or block heavy assets while leaving HTML untouched.

```bash
# Stub /api responses but let CSS/images load normally
npx agent-browser network route "**/api/**" --body '{"ok":true}' --resource-type xhr,fetch

# Strip images for a faster perf reproduction
npx agent-browser network route "**" --abort --resource-type image
```

`route` returns `Done` whether or not it actually intercepts. **Always verify** with `network requests --filter` after triggering the request:

```bash
npx agent-browser network requests --clear
# ... trigger the call ...
npx agent-browser network requests --filter "/api/"
# If the request shows up with a real status, the route did NOT intercept.
```

There are open questions about `--body` reliability on Vite-dev-server origins on 0.27.0 — see [reference/commands.md](./commands.md) for the caveat. Verify before relying on either.

## Init scripts (0.27+)

Need a global set, a probe installed, or DevTools hooks injected **before** app code runs? Register an init script at `open` time:

```bash
# Repeatable; runs before every navigation
npx agent-browser open https://app.example.com \
  --init-script /tmp/seed-test-user.js \
  --init-script /tmp/probe-router.js

# Or via env, comma-separated
AGENT_BROWSER_INIT_SCRIPTS=/tmp/a.js,/tmp/b.js npx agent-browser open https://...

# Built-in features
npx agent-browser open https://... --enable react-devtools
```

Each registration returns an id; remove with `npx agent-browser removeinitscript <id>`. Init scripts are launch-time — to add one to a running daemon, `close` and re-`open`.

## Version discovery

Record the `agent-browser` version in registry entries so behavior drift is traceable:

```bash
npx agent-browser --version
```

The CLI ships its own version-matched skill docs (`npx agent-browser skills get core --full`). Worth a one-time read after a major version bump to spot new commands not yet covered here.
