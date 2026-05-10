---
purpose: "Committed, shared catalog of CLI-level and generic-web gotchas for the agent-browser skill. Add here (NOT in .registry/) whenever you discover a behavior that will trip up future agents regardless of site. Grows over time; review when something surprises you."
scope: "agent-browser CLI behavior + web/a11y fundamentals that apply to any site"
not_here: "Site-specific selectors, workflows, credentials — those belong in .registry/<slug>.md"
---

# Generic gotchas

Behaviors that tripped up prior sessions regardless of which site was being automated.

**When to add to this file:** you hit something that would have tripped you up on any site — CLI quirks (refs, flags, daemon behavior), generic web/a11y fundamentals, sandbox/environment issues. If the next person to use this skill on a totally different site would also benefit from knowing it, it belongs here.

**When NOT to add to this file:** site-specific selectors, login flows, or UI quirks — those belong in the per-site registry entry at `.registry/<slug>.md`. A good heuristic: does the note mention a specific URL, brand, or domain concept? If yes, it's site-specific.

This file is committed to git and shared across everyone using the skill. Be terse and concrete — lead each entry with the observable symptom, state the workaround as a command or selector, not prose.

## Refs are ephemeral

Every `snapshot` generates fresh refs. Any DOM mutation (click, fill, navigation, even some hover-triggered state changes) invalidates the prior ref set. **Re-snapshot before referencing an element after any action that might have changed the page.**

Never hardcode a ref across sessions. Always capture **CSS selectors** for stable elements in the site registry.

## `--headed` is ignored on a running daemon

If the daemon is already up, `open <url> --headed` will reuse the existing (possibly headless) browser. You'll see:

```
--headed ignored: daemon already running. Use 'agent-browser close' first to restart with new options.
```

To switch modes, `close` and then `open`.

## `fill` does not clear `contenteditable`

On native `<input>` / `<textarea>`, `fill` clears first, then types — the expected behavior.

On `contenteditable` elements (TipTap, ProseMirror, Slate, Lexical, CodeMirror, Monaco…), `fill` **appends** to existing content. To clear:

```bash
npx agent-browser eval "document.querySelector('[contenteditable=true]').innerHTML = '<p></p>'"
npx agent-browser click @<ref>     # re-focus
npx agent-browser type @<ref> "new text"
```

Or for a specific editor, look up its API (e.g. TipTap's `.commands.setContent('')`).

## `type` works on `contenteditable` via `@ref`

You don't need to fall back to CSS selectors for rich-text editors. `type @<ref> "..."` works — just `click @<ref>` first to focus.

## Enter in rich-text editors usually creates a newline

`press Enter` in a TipTap/ProseMirror/etc. input almost always inserts a newline rather than submitting. To submit, locate and click the Send / Submit button explicitly.

Always verify this per site — it's a common default but not universal. Record the answer in the site registry.

## Clicks on `[disabled]` elements silently succeed

`click @<ref>` on a disabled button returns `Done` with no error and has no effect. If behavior seems wrong, check state first:

```bash
npx agent-browser is enabled @<ref>
```

## `get text @<ref>` returns empty for icon-only elements

Buttons rendered as icon-only (no text-node child, just an SVG) return an empty string from `get text`. Use the a11y name from the snapshot (e.g. `button "Close" [ref=e12]`) or `eval` the element's outer HTML.

## `wait <selector>` hangs for ~2.5 minutes on a miss

If the selector never matches, `wait` blocks for the full internal timeout (~150s) before failing with `Resource temporarily unavailable`. During that time other CLI calls may be delayed.

Mitigations:

- Use `wait <ms>` (time-based) when you don't have a known-good selector.
- Verify the selector exists before waiting: `npx agent-browser get count "<css>"`.
- Prefer snapshot-based polling: short `wait 500` + `snapshot --interactive | grep ...` loop.

## `find <kind> <value>` without an action returns no useful output

`find text "Foo"` on its own prints `Done` — it doesn't tell you the ref. Either chain an action (`find text "Foo" click`) or use `snapshot --interactive | grep "Foo"` for discovery.

## Accessible name ≠ `aria-label` attribute

The snapshot shows each interactive node's **accessible name** (e.g. `button "Add member"`, `textbox "Email address"`). That name comes from the W3C AccName algorithm, which considers — in order — explicit `aria-labelledby`, `aria-label`, an associated `<label>`, and finally the element's visible text content. **Most of those sources are not `aria-label` attributes.**

Consequences when picking a CSS selector:

- Seeing `button "Send"` in the snapshot does **not** mean `button[aria-label="Send"]` matches. If the button has a visible text child (`<button>Send</button>`), there is usually no `aria-label` attribute — adding one would be redundant (and if it disagreed with the visible text, an anti-pattern that overrides it for assistive tech).
- Seeing `textbox "Email address"` does **not** mean `[aria-label="Email address"]` matches. Most `<input>`-with-`<label>` forms use `<label for="…">` to associate the name, no `aria-label` in sight.

Where `aria-label` *is* typically present:

- Icon-only buttons that have no visible text (a sidebar `<button><Icon/></button>` labelled "Home" is the canonical case).
- Elements whose visible text is too cryptic for assistive tech (e.g. a disclosure `▼` that should announce as "Expand menu").

How to pick a selector:

1. **Has visible text?** Use text match (`find text "Send" click`) or a ref from the snapshot.
2. **No visible text, icon-only?** Try `[aria-label="…"]`.
3. **Form input?** Try `input[type="…"]`, `input[name="…"]`, or a ref — not `[aria-label]`.

Verify with `eval "document.querySelector('[aria-label=…]') !== null"` before committing to a selector strategy.

## `--selector` uses CSS, not ARIA roles

The snapshot output shows ARIA roles (`complementary`, `navigation`, `region`) derived from semantic HTML elements (`<aside>`, `<nav>`, `<section>`). But `--selector` expects CSS:

- ✅ `--selector "aside"` / `--selector "main"` / `--selector "[role=complementary]"` (if the `role` attribute is explicit)
- ❌ `--selector "complementary"` (this is an ARIA role name, not a CSS selector)

## Don't `close` between tasks — that's what spawns extra browser windows

The daemon is **single-tab and persistent**. `open <new-url>` while it's running navigates the existing window — same browser, cookies/localStorage retained. `close` is what destroys the window; the next `open` then spawns a fresh one.

If you find the agent has produced many browser windows for the same site, the cause is almost always: every task ended with `close` and started with `open`. Stop closing.

- ✅ `open <url>` repeatedly across tasks → reuses the same window.
- ❌ `close` → `open` between tasks → fresh window, fresh cookies, you have to log in again.

`close` is the right call only when: the user asks, the session is genuinely done, you're switching `--session` name, the daemon is wedged, or you need to change a daemon-launch flag (`--headed`, `--enable react-devtools`, `--init-script`).

See [reference/patterns.md](./patterns.md) §"Reusing a running daemon" for the full procedure.

## Many buttons have no accessible name

Close/dismiss X buttons, icon-only action buttons, and similar often appear in the snapshot as just `button [ref=eN]` with no name. Identify them by position — adjacent to a heading, at the end of a toolbar, etc.:

```
- heading "Panel title" [ref=e3]
- button [ref=e4]           <- likely the close X
```

Record the CSS selector in the site registry once discovered.

## Snapshot output is YAML-adjacent, not valid YAML

The snapshot uses a YAML-like indented tree but isn't parseable by a YAML library. If you need structured data, use `--json` instead of trying to parse the textual output.

## Chained commands fail fast

In `cmd1 && cmd2 && cmd3`, if `cmd1` errors, `cmd2` and `cmd3` never run. This is usually what you want, but means a silent click (see above) won't short-circuit the chain — the chain completes "successfully" while the click did nothing.

## The daemon is single-tab

`agent-browser` operates on one tab. Opening links that spawn new tabs will leave the daemon on the original tab. Use `open <url>` to navigate programmatically instead of relying on `target="_blank"` links.

## Daemon shutdown is `close`, not `stop`

`npx agent-browser close` shuts the daemon. `stop` is not a subcommand — guessing it prints the top-level help and exits non-zero. If you need the CLI's own authoritative list, `npx agent-browser --help` is cheap.

## `type` without a ref treats the text as a ref

`npx agent-browser type "some text"` does **not** type into the focused element. The first positional argument is always interpreted as a ref (or CSS selector), so `"some text"` is looked up as an element reference and the command fails with `Element not found`.

Always provide the target explicitly:

```bash
npx agent-browser type @e12 "hello"          # by ref
npx agent-browser type '[contenteditable]' "hello"  # by CSS
```

`click @<ref>` first to focus, then `type @<ref> "text"` — the ref must appear in both calls.

## `select=eq(n\,N)` frame numbers match the recording's native FPS, not extracted-frame numbers

When you extract frames with `ffmpeg -vf "fps=4 …"`, the output files are numbered 0001–NNNN at 4 fps. But if you later try to extract a specific frame from the **original recording** using `select=eq(n\,N)`, `N` is a 0-based index into the recording's native frame rate (often 10–30 fps), not the 4-fps sequence.

Example: recording at 10 fps, extracted frame `0720` (4-fps output) corresponds to time `(720-1)/4 = 179.75 s` → native frame `179.75 × 10 = 1798`.

To extract a specific full-resolution frame by time, use the `-ss` flag instead of `select`:

```bash
ffmpeg -ss 179.75 -i recording.webm -vframes 1 /tmp/frame-at-180s.png
```

## Screenshot paths resolve relative to the daemon's CWD

`npx agent-browser screenshot out.png` writes `out.png` relative to wherever the daemon was launched, not your current shell. **Always pass an absolute path** (`/tmp/out.png`).

## `react tree` without `--json` silently emits nothing useful (0.27.0)

`npx agent-browser react tree` (no flag) prints `✓ Done` and no tree. The other `react` subcommands behave normally; this one is broken in text mode. Always pass `--json`:

```bash
npx agent-browser react tree --json | jq '.data.tree[] | {id, name, parent}' | head
```

## `react *` subcommands require `--enable react-devtools` at `open` time (0.27+)

The React DevTools hook must be installed before the app mounts. Without it, `react tree`, `react inspect`, `react renders`, and `react suspense` either return nothing or fail. The fix is launch-time — you can't bolt the hook onto a daemon that already started without it:

```bash
npx agent-browser close
npx agent-browser open https://app.example.com --enable react-devtools
npx agent-browser react tree | head
```

Same applies to `--init-script` — it's a daemon-launch flag, not retrofittable. To add or change one, `close` and re-`open`.

## `vitals` needs interaction before CLS/INP have meaningful values (0.27+)

LCP, FCP, and TTFB are observable from a single load. **CLS and INP only accumulate when the page is interacted with or scrolled**. Calling `vitals` on a freshly-opened idle page reports near-zero CLS/INP regardless of how janky the app actually is. Run the flow you care about first, then call `vitals --json`.

## `pushstate` only helps when the app implements client routing (0.27+)

`pushstate <url>` triggers SPA-style navigation: it auto-detects `window.next.router.push` (Next.js) and otherwise dispatches `history.pushState` + `popstate`/`navigate` events. On a non-SPA page (server-rendered, full reload per nav), it changes the URL but the app won't react — the page stays as-is. Use `open` for hard navigation; reach for `pushstate` only when you specifically want to test client-routing behavior.
