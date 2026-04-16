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

## Version discovery

Record the `agent-browser` version in registry entries so behavior drift is traceable:

```bash
npx agent-browser --version
```
