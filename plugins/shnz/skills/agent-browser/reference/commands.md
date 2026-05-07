# `agent-browser` CLI reference

All commands are invoked via `npx agent-browser <subcommand> [args]`. The CLI talks to a persistent daemon over a Unix socket, so commands are fast (~0.4s per op) but the daemon must be startable.

This reference covers the subcommands you'll use most. For authoritative help run `npx agent-browser --help` or `npx agent-browser <subcommand> --help`. The CLI also ships its own version-matched skill docs — `npx agent-browser skills get core --full` is worth a one-time read when the version moves.

## Lifecycle

### `open <url> [flags]`

Starts the daemon (if not running) and navigates to the URL.

- `--headed` opens a visible browser window. **Ignored if the daemon is already running** — close and reopen to change mode.
- `--init-script <path>` (repeatable) registers a page-init script that runs before *every* navigation in the session. Must be passed at `open` time — re-`open` to add more.
- `--enable <feature>` (repeatable; comma-separated also accepted) loads a built-in init script. The one you'll actually use is `react-devtools`, which is required before any `react` subcommand will work.
- If the daemon is already running, `open <url>` navigates instead of relaunching. Cookies/session state persist. Daemon-time flags (`--headed`, `--init-script`, `--enable`) require a `close` first.

```bash
npx agent-browser open https://example.com --headed
npx agent-browser open https://app.example.com --enable react-devtools
npx agent-browser open https://app.example.com --init-script /tmp/probe.js
```

### `close`

Stops the daemon and closes the browser. Session state is lost.

```bash
npx agent-browser close
```

## Inspection

### `snapshot [flags]`

Dumps the current page's accessibility tree. Every interactive node is assigned an ephemeral ref like `e12`.

| Flag | Effect | When to use |
|------|--------|-------------|
| *(none)* | Full a11y tree (hundreds of lines typical) | Need structural context — nesting, headings, static text |
| `--interactive` | Only buttons, inputs, links | **Default first pass** — quickest way to find what to click |
| `--compact` | Drops empty structural nodes from full tree | Rare — marginal improvement |
| `--selector <css>` | Scope to a CSS subtree | Target a specific panel (`--selector "main"`) |
| `--urls` | Include `href` on links | When you need to see where links point |
| `--depth N` | Cap tree depth | Rarely useful below ~4 |
| `--json` | Machine-readable JSON with `refs` map + snapshot text | Programmatic use |

`--selector` takes **CSS selectors**, not ARIA roles. The snapshot text shows ARIA roles (e.g. `complementary`, `navigation`) but those come from semantic HTML elements — use the element name (`aside`, `nav`) or an explicit `[role=...]` attribute.

```bash
npx agent-browser snapshot --interactive
npx agent-browser snapshot --selector "main"
npx agent-browser snapshot --urls | grep "Sign in"
```

### `get <prop> @<ref>` / `get <prop> <css>`

Read a property from an element.

- `get text @e12` — text content (empty for icon-only buttons)
- `get count "button.primary"` — count of elements matching a CSS selector
- `is enabled @e12` — returns `true`/`false`

### `find <kind> <value> [<action>]`

Locate an element by text, role, or label.

- `find text "Sign in" click` — combine with an action (`click`, `fill ...`, `type ...`)
- `find text "Sign in"` on its own just prints `Done` — no ref info. Use `snapshot --interactive | grep "Sign in"` for discovery.
- **Flakiness caveat**: `find text` may return `Element not found` even when the element is present in the snapshot, especially right after a DOM mutation. If you hit that despite seeing the text in a fresh snapshot, fall back to clicking via the element's `@ref`.
- **First-match caveat**: `find text "X" click` clicks the **first** element in document order with text matching `X`. If the same text appears more than once on the page (common: headers and forms both have "Sign in" / "Submit" / "OK"), this will collide. Use a ref from a fresh snapshot when text is non-unique.

## Interaction

### `click @<ref>` / `click <css>`

Dispatches a click. **Returns `Done` silently even on `[disabled]` elements** — always check `is enabled` first if behavior is suspect.

### `fill @<ref> "<value>"` / `fill <css> "<value>"`

- On `<input>` / `<textarea>`: clears existing value, then types. Correct default.
- On `contenteditable` elements (TipTap, ProseMirror, Slate, etc.): **appends** instead of clearing. Clear manually first — see [gotchas.md](./gotchas.md).

### `type @<ref> "<value>"` / `type <css> "<value>"`

Types without clearing. Works on both standard inputs and `contenteditable` (you may need to `click` the element first to focus it).

### `press <key>`

Send a key. Common keys: `Enter`, `Escape`, `Tab`, `ArrowDown`, `Backspace`.

Beware: in rich-text editors `press Enter` commonly creates a newline rather than submitting. Check site-specific behavior before assuming.

## Waiting

### `wait <ms>`

Time-based wait. Always safe.

```bash
npx agent-browser wait 1500
```

### `wait <css-selector>`

Wait for a selector to appear. **Hangs for ~2.5 minutes if the selector never matches**, and can block subsequent CLI calls during that time. Only use with a selector you're confident will appear.

## Output capture

### `screenshot <absolute-path>`

Saves a PNG. Paths are resolved relative to wherever the daemon is running, **not** the caller's CWD — always use absolute paths.

```bash
npx agent-browser screenshot /tmp/check.png
```

### `record start <absolute-path.webm>` / `record stop`

Records a WebM video of the session. A few seconds of interaction ≈ 300KB.

```bash
npx agent-browser record start /tmp/flow.webm
# ... commands ...
npx agent-browser record stop
```

## Scripting

### `eval "<js>"`

Execute arbitrary JS in the page context. Returns whatever the expression evaluates to.

```bash
npx agent-browser eval "document.title"
npx agent-browser eval "!!document.querySelector('.my-class')"
npx agent-browser eval "document.querySelector('[contenteditable=true]').innerHTML = '<p></p>'"
```

## React introspection (0.27+)

These commands require the React DevTools hook to have been installed before the page mounted. That means a fresh session opened with `--enable react-devtools` (or an equivalent `--init-script`) — they will silently return nothing if you try to bolt them onto a daemon that started without it.

### `react tree [--json]`

Returns the React component tree. **Use `--json`** — without the flag, the CLI (as of 0.27.0) prints only `✓ Done` and emits nothing useful. The JSON shape is `{ data: { tree: [...] } }`; each node has `depth`, `id`, `parent`, `name`. `id` is the **fiber id** the other `react` subcommands take.

```bash
npx agent-browser react tree --json | jq '.data.tree | length'
# Discover a fiber id, then:
npx agent-browser react inspect 47
```

A real-world tree is a few hundred fibers including provider chains (~14KB JSON for a small app home route).

### `react inspect <id>`

Inspect one fiber: **props, hooks, state, source location, and the rendered-by ancestor chain**. The ancestor chain is the killer feature — it answers "why is this component getting these props?" without launching the React DevTools UI, and confirms file:line for any rendered component.

```bash
npx agent-browser react inspect 47
```

### `react renders start` / `react renders stop [--json]`

Profile re-renders via `onCommitFiberRoot`. Start before the interaction, stop after, read the report.

`--json` returns a markdown table sorted by total render time, plus FPS stats and a "top change reason" per component — far cheaper than the React DevTools profiler tab. Captures hundreds of renders / dozens of components on a multi-second interaction.

```bash
npx agent-browser react renders start
npx agent-browser click @e3
npx agent-browser wait 500
npx agent-browser react renders stop --json
```

### `react suspense [--only-dynamic] [--json]`

Walks Suspense boundaries and prints a classifier report. `--only-dynamic` hides "static" boundaries (boundaries that never suspended in this session), which is usually what you want when investigating a slow first paint.

```bash
npx agent-browser react suspense --only-dynamic --json
```

## Web Vitals (0.27+)

### `vitals [url] [--json]`

Reports Core Web Vitals — **LCP, CLS, TTFB, FCP, INP** — for the current page (or `url` if provided). When the build is a profiling build, also reports React hydration phase timings.

```bash
npx agent-browser vitals --json
npx agent-browser vitals https://example.com --json
```

CLS and INP need user interaction or scrolling to accumulate values — kicking off the flow you care about and *then* calling `vitals` is more useful than calling it on a freshly-loaded idle page.

## SPA navigation (0.27+)

### `pushstate <url>`

Triggers client-side navigation **without a full page reload**. Auto-detects `window.next.router.push` (Next.js — this also kicks off the RSC fetch); falls back to `history.pushState` + dispatching `popstate` / `navigate` events for other frameworks.

```bash
npx agent-browser pushstate /dashboard
npx agent-browser wait 800
npx agent-browser snapshot --interactive
```

Use this instead of `open` when you want to test an SPA's *client routing* behavior — e.g. layout chrome stability across route changes — and not its initial-load behavior.

## Init scripts (0.27+)

Page-init scripts run before any user code on every navigation in the session.

- Pass at daemon launch with `npx agent-browser open <url> --init-script <path>` (repeatable) or `--enable <feature>` for built-ins like `react-devtools`.
- Env equivalents: `AGENT_BROWSER_INIT_SCRIPTS=/path/a.js,/path/b.js`, `AGENT_BROWSER_ENABLE=react-devtools`.
- Each registration returns an id. Remove with `npx agent-browser removeinitscript <id>`.

Init scripts are how you patch globals (e.g. seed `window.__TEST_USER__`), install probes, or enable dev hooks (React DevTools) before app code runs. They are **not** retrofittable to an already-loaded page — that's what `eval` is for.

## Network route filtering by resource type (0.27+, ⚠️ unverified)

`network route` advertises `--resource-type <csv>` to restrict matching to specific Chrome resource types — e.g. only intercept images, fonts, or XHR. Values match Chrome's resource type names: `document, stylesheet, image, media, font, script, texttrack, xhr, fetch, eventsource, websocket, manifest, other`.

```bash
# Block all images on a domain
npx agent-browser network route "https://cdn.example.com/**" --abort --resource-type image

# Stub only the fetch/xhr calls to /api, leave assets alone
npx agent-browser network route "**/api/**" --body '{"ok":true}' --resource-type xhr,fetch
```

**Caveats observed on 0.27.0**:

- The flag is accepted but **missing from `network route --help`** — possible doc drift, possible incomplete wire-up.
- At least one tester saw `--body` fail to intercept any of four same-origin patterns against a Vite dev server, both with and without `--resource-type`. Symptom: `route` returns `Done`, but every matching request still hits the upstream server.

**Always verify** the route is firing before relying on it:

```bash
npx agent-browser network requests --clear
# ... trigger the request you expect to be stubbed ...
npx agent-browser network requests --filter "/api/"
# If the request appears here with a real status, the route did NOT intercept.
```

Without `--resource-type`, every matching request is *supposed to be* routed — same verification step applies.

## cURL / Cookie-header cookie import (0.27+)

`cookies set` accepts a file via `--curl <file>` and auto-detects the format:

- **JSON** — array of cookie objects (`{name, value, domain, path, ...}`). The shape EditThisCookie / DevTools "Application → Cookies → export" produce. Domain/path are read from the JSON; no `--domain` needed.
- **cURL command** — paste the entire `curl 'https://...' -H 'Cookie: a=1; b=2' ...` line. Useful when copying "Copy as cURL" from DevTools Network tab.
- **Cookie header** — a bare `Cookie: a=1; b=2` line, or just `a=1; b=2`. Pair with `--domain <host>` so the imported cookies actually apply.

```bash
npx agent-browser cookies set --curl /tmp/copied-as-curl.sh
npx agent-browser cookies set --curl /tmp/cookies.json
npx agent-browser cookies set --curl /tmp/cookie-header.txt --domain app.example.com
```

This is the fast path for "I'm logged in in my real browser; let me hand the same session to the agent" — much less ceremony than the auth vault for one-off scripts.

Note: `--curl` is **missing from `cookies --help`** on 0.27.0 but is functional. Don't be deterred by its absence from the help output.

## Dashboard

`npx agent-browser dashboard [start]` runs the observability UI (default port 4848). As of 0.27 it works correctly behind a reverse proxy (relative URLs, proxy-aware base path) — useful when running the daemon on a remote dev box and tunneling the dashboard through ngrok/Tailscale/an ingress.

### Chaining

Chain with `&&` inside a single shell call to avoid per-command tool overhead:

```bash
npx agent-browser click @e13 && npx agent-browser wait 800 && npx agent-browser snapshot --interactive
```

Typical click + wait + snapshot ≈ 0.8s end-to-end.

## Environment

### Sandbox

The daemon's Unix socket is blocked by common agent sandboxes. If you see `Daemon failed to start` despite the daemon running, the sandbox is the culprit. For Claude Code, set `dangerouslyDisableSandbox: true` on the `Bash` invocation. For other agents, consult your host's equivalent escape hatch.

### npm cache

First-time `npx` may fail with `EPERM` about the npm cache. Workaround:

```bash
npm_config_cache=/tmp/.npm-agent-browser npx --yes agent-browser <command>
```

### Pinning a version

`npx --yes agent-browser@<version> <command>` pins to a specific release. Useful if you've recorded the working version in a site registry entry and want reproducibility.
