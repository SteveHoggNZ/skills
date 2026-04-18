# Slide mode (present mode)

The site should be navigable as both a polished single-page web app **and** a slide deck.

- Arrow-key / space / click navigation through the content in a landscape slide-by-slide view.
- Same content as the scroll site — zero content duplication.
- Modern polish preserved (typography, spacing, badges, callouts all look right in both modes).
- Escape returns to normal mode.

## Design

The implementation lives in `assets/script.js`, bundled with the tab-switching logic. Full source is inlined in [scaffold.md](./scaffold.md) §`assets/script.js`.

Key decisions:

- **`<h2>` boundaries drive slides.** Each `<h2>` inside any `<div class="page">` starts a new slide; preceding content up to the next `<h2>` is the slide body. This falls out naturally from good page structure (which the Vision/Roadmap/Map templates already enforce).
- **Flat deck across the whole site.** Slides are flattened across all `.page` divs in nav order. Walking the deck end-to-end walks the whole concept — Vision → Roadmap → Map — in the order the author chose. This matches how a presenter uses it: "let me walk you through this".
- **Host-page indicator.** The slide counter shows `3 / 24 · roadmap` so the viewer knows which section a slide came from.
- **Deep-linkable.** `?present=1#slide-7` enters present mode at slide 7. Handy for sending a colleague straight to a specific frame.

## Why not reveal.js / Slidev

Both are excellent but reformat content into slide-specific source (HTML `<section>` in reveal, special Slidev markdown). That duplicates authoring: the same concept has to be written twice — once for the web site, once for the deck. This skill's contract is **one source of truth**: the content in `<div class="page">` sections is both the website and the deck.

The custom implementation is ~180 lines of vanilla JS. If a user later wants reveal.js-level transitions or speaker notes, swap it out as part of a `skill-iterate` pass — the slide-boundary convention (`<h2>`) means the content is already in the right shape.

## Behaviour

- Nav has a **Present** button at the right end. Clicking it enters slide mode.
- In slide mode:
  - Nav and footer are hidden; the active `.page` becomes a fixed landscape stage, centered.
  - One `<h2>`-bounded slide is visible at a time.
  - `→` / `Space` / click anywhere (except on links/buttons) → next. `←` → previous. `Home` / `End` → first / last.
  - A `3 / 24 · roadmap` counter sits in the corner.
  - Escape exits back to normal mode; the original tab is restored and scroll position is preserved.
- URL gets `?present=1#slide-N` while in slide mode.

## Customisation

If a deck feels wrong in a particular site, adjust one of:

- **Boundary tag.** If the user wants coarser slides (one per section = `<h1>` boundaries), change `tagName === 'H2'` in `buildSlides()` to `'H1'`. Finer slides (one per sub-heading = `<h3>`) is rarely a good idea — readability drops.
- **Stage aspect ratio.** CSS variable in `.slide-stage`: `max-height: min(85vh, calc(90vw * 9 / 16))`. 16:9 is the default. Widescreen (`21 / 9`), square, or portrait are all one-line changes.
- **Transitions.** The default has no animation — content loads instantly. Adding a fade is one line: `.slide-stage { transition: opacity 0.2s; }` plus an `opacity: 0` → `opacity: 1` toggle in `renderSlide()`. Don't add motion in v1; it masks content while loading.
- **Slide counter position.** `.slide-counter` is `position: fixed; bottom: 1rem; right: 1.25rem`. Move to top-left, top-right, or centre-bottom to taste.

## What NOT to do

- **Don't author slide-specific markup** (e.g. `---` separators, `<section>` wrappers). The whole point is one source of truth.
- **Don't introduce transitions / animations in v1.** Motion makes content harder to read cold and adds bug surface. Add them by a later `skill-iterate` pass only if presenters actually ask for them.
- **Don't try to fit overlong slides by shrinking text further.** If a `<h2>` section is too long for one slide, split it into two `<h2>`s — that's also better for the normal view.
- **Don't conflate slide mode with PDF export.** The PDF is for offline distribution; slide mode is for live presentation. Different constraints, different code paths. See [pdf-export.md](./pdf-export.md).
- **Don't load content dynamically in present mode.** All slides must be present in the DOM when the page loads — a `fetch`-then-render flow breaks `file://`, breaks PDF capture, and breaks the deep-link.
