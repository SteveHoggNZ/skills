# `agent-browser` CLI reference

All commands are invoked via `npx agent-browser <subcommand> [args]`. The CLI talks to a persistent daemon over a Unix socket, so commands are fast (~0.4s per op) but the daemon must be startable.

This reference covers the subcommands you'll use most. For authoritative help run `npx agent-browser --help` or `npx agent-browser <subcommand> --help`.

## Lifecycle

### `open <url> [--headed]`

Starts the daemon (if not running) and navigates to the URL.

- `--headed` opens a visible browser window. **Ignored if the daemon is already running** — close and reopen to change mode.
- If the daemon is already running, `open <url>` navigates instead of relaunching. Cookies/session state persist.

```bash
npx agent-browser open https://example.com --headed
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
