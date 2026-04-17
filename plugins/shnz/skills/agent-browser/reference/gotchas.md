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

## Session persists across `open` navigations, not across `close`

- `open <new-url>` while the daemon is running: cookies and localStorage persist. You stay logged in.
- `close` then `open`: fresh browser, fresh cookies. Plan login steps accordingly.

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

## Screenshot paths resolve relative to the daemon's CWD

`npx agent-browser screenshot out.png` writes `out.png` relative to wherever the daemon was launched, not your current shell. **Always pass an absolute path** (`/tmp/out.png`).
