# Create Concept Website

Scaffold and author a static concept website that gets a group of people on the same page about a concept, by explaining it **top-down and bottom-up**:

- **Top-down (the why)** — the **Vision** section: the destination state, the "art of the possible", the strategic frame. Narrative, aspirational, makes the concept feel real.
- **Bottom-up (the how)** — the **Roadmap** section: tactical waves of adoption with checkboxes and success criteria, and the **Map** section: the layers / stages the concept decomposes into, with per-layer readiness.

If the site only does the top-down, people nod but don't act. If it only does the bottom-up, people execute without understanding why. Both halves are load-bearing.

The reference implementation is [https://stevehoggnz.github.io/ai-sdlc/](https://stevehoggnz.github.io/ai-sdlc/) — a site teaching the AI-native SDLC concept. It's a **single-page HTML app** with JS-driven tab switching; this skill generalises that shape for any concept.

## Output shape

A **single-page HTML site** — zero build step, zero runtime dependencies. Double-click `index.html` and the site works.

```
<target-dir>/
├── index.html            # one page containing every nav section as a <div class="page" id="...">
├── assets/
│   ├── style.css         # base + slide-mode + print CSS (all in one file)
│   └── script.js         # tab switching + slide/present mode
└── data/
    └── intake.yml        # user's intake answers, retained for future iterations
```

Optional additions (only when the material supports them):

- `sdlc-map.html` (or similar) — a dedicated companion page if the Map is long and benefits from its own URL. The reference site does this for the SDLC Map.
- `onepager-<topic>.html` — dense printable one-pager per audience (managers, SREs, etc.).
- `scripts/build-pdf.mjs` + `package.json` — Puppeteer-based PDF builder producing `assets/<slug>.pdf` (see [reference/pdf-export.md](./reference/pdf-export.md)).

### Why not Jekyll / Astro / 11ty

Concept sites are read a few times, forked/copied often, and handed around. A zero-build HTML file travels. A Jekyll source tree requires Ruby ≥ 3.0; Astro requires Node + a build step; both add friction precisely when the site is most valuable (the first 50 reads by stakeholders on unfamiliar machines). Keep the source the deliverable.

## What the HTML shell looks like (summary)

```html
<header class="site-header">
  <a class="logo" href="#vision">{{title}}</a>
  <nav class="tab-nav" aria-label="Primary">
    <button class="tab-btn" data-page="vision" aria-current="page">Vision</button>
    <button class="tab-btn" data-page="roadmap">Roadmap</button>
    <button class="tab-btn" data-page="map">Map</button>
    <button class="present-toggle">Present</button>
  </nav>
</header>
<main id="main">
  <div class="page active" id="vision">…</div>
  <div class="page"        id="roadmap">…</div>
  <div class="page"        id="map">…</div>
</main>
```

`script.js` toggles `.active` on the right `<div class="page">` when a tab button is clicked or when the URL hash changes. `style.css` handles layout, typography, badges, pullquotes, print CSS, and present-mode styles. Full templates in [reference/scaffold.md](./reference/scaffold.md).

## Two cross-cutting features (ship by default)

- **Slide / "Present" mode** — the nav has a "Present" button; pressing it switches the whole site into a linear landscape deck driven by `<h2>` boundaries across all `.page` divs. Arrow keys / space / click advance; Escape exits. Same content, new view. See [reference/slide-mode.md](./reference/slide-mode.md).
- **PDF export** — the print stylesheet always works (Cmd+P → Save as PDF). Optionally, a Puppeteer build script (`npm run pdf`) produces `assets/<slug>.pdf` with every section concatenated, linked from the nav. See [reference/pdf-export.md](./reference/pdf-export.md).

## Procedure

The procedure is **intake → outline → scaffold → write → preview**. Do not skip intake. Do not write before outlining. The failure mode this skill exists to prevent is generic-sounding filler that could describe any concept.

### 1. Intake

Run the questionnaire in [reference/intake.md](./reference/intake.md). You need enough material to write the three load-bearing sections (Vision, Roadmap, Map) without fabricating. The minimum viable intake is:

- **Concept slug + one-liner.**
- **Audience.**
- **Vision material**: destination state, pillars / principles, why now.
- **Roadmap material**: waves of adoption with outcomes and success criteria.
- **Map material**: the layers / stages with readiness per layer.

If any of the three is missing, stop and ask. Writing with incomplete material produces hedged, abstract prose that defeats the point.

Convert any material the user hands you (docs, slides, chat logs, repo README) into the intake fields before moving on. Quote or cite specific lines when you can — those become the concrete examples that make the site feel real.

**Non-interactive runs** (probes, autonomous agents, or runs where the user attaches source material and won't be answering questions): extract the intake fields from the source rather than asking. Flag any field you had to *derive* rather than *extract* in the final summary so the author can confirm later.

### 2. Outline

Before scaffolding or writing, draft:

- **One-line purpose** for each section on the site (Vision, Roadmap, Map, plus any companion pages).
- **Section list** inside Vision, Roadmap, Map (the `<h2>`s).
- **Nav order** (the reference site uses: Vision → Roadmap → (deep-dives) → Map; mirror that).
- **Voice & metaphors**: pick 1–3 metaphors from the intake that you'll reuse throughout the site (e.g. "execution is cheap, clarity is expensive"). See [reference/voice.md](./reference/voice.md).

Show the outline to the user. Get agreement before scaffolding. This is the cheapest point to course-correct.

### 3. Scaffold

Follow [reference/scaffold.md](./reference/scaffold.md) to create:

1. Target directory (`mkdir -p <target-dir>/{assets,data}`).
2. `index.html` with the shell above, tab buttons reflecting the nav order, and empty `<div class="page" id="...">` blocks per nav item.
3. `assets/style.css` with base styles + slide-mode + print CSS (all in one file for zero-build simplicity).
4. `assets/script.js` with tab switching + present-mode logic.
5. `data/intake.yml` with the intake answers in the canonical schema (see [reference/intake.md](./reference/intake.md) §"Canonical schema").

Do **not** fill section bodies yet. Keep scaffold and content as separate steps so the user can eyeball the nav + tab-switch behaviour before you commit to prose. Opening `index.html` at this point should show an empty site with working tabs.

### 4. Write

Write the section HTML **inside the appropriate `<div class="page" id="...">` block** in `index.html`. Each section content starts with an `<h1>` and uses `<h2>` for sub-sections (the `<h2>`s are the slide boundaries in present mode).

Order (Vision last is deliberate — it's the hardest and benefits from having Map and Roadmap drafted first):

1. **Map section** (`<div id="map">`) — see [reference/page-map.md](./reference/page-map.md).
2. **Roadmap section** (`<div id="roadmap">`) — see [reference/page-roadmap.md](./reference/page-roadmap.md).
3. **Vision section** (`<div id="vision">`) — see [reference/page-vision.md](./reference/page-vision.md).
4. **Homepage content** — render this as the initially-visible pane. The simplest choice: put Vision *first* in nav order and make it the default `.active` page. No separate `index`-only content. If the user insists on a distinct landing section, add a `<div class="page active" id="home">` with a hook + three cards linking to `#vision`, `#roadmap`, `#map`. See [reference/scaffold.md](./reference/scaffold.md) §"Landing section (optional)".

Apply the voice and visual language consistently. Every section should:

- Open with a one-sentence purpose (right after the `<h1>`).
- Use concrete examples from the intake, not hypotheticals.
- Reuse the 1–3 chosen metaphors.
- Include at least one visual element (table, checklist, badge row, diagram, callout).

### 5. Preview & iterate

- Open the file directly: `open index.html` on macOS, or double-click in Finder. The site works from `file://`.
- For a cleaner dev loop (live reload + correct CORS for any future fetch), a throwaway static server works: `python3 -m http.server 8000 --directory <target-dir>` and visit `http://localhost:8000/`. Unlike the Jekyll case, serving the target dir directly is **fine** — the files served are actual HTML, not markdown source.
- Click through every tab. Confirm hash-based deep-linking (`index.html#roadmap` should land on the Roadmap tab).
- **Verify slide mode**: click "Present", confirm arrow keys walk through every `<h2>` across the whole site, confirm Escape exits cleanly.
- **Verify PDF**: `Cmd+P` and check that nav chrome / present button / footer are hidden and tables/callouts don't split awkwardly. If the user opted into the Puppeteer builder, run `npm run pdf` and open the output.
- Read each section aloud (mentally). If a chunk hedges or sounds generic, rewrite it with a concrete example from the intake, or cut it.
- Offer the user:
  - A deployment hint (GitHub Pages: push the target dir to any branch, enable Pages; or `netlify deploy`; or copy the folder anywhere — it's portable).
  - The optional Puppeteer PDF setup if they skipped it during scaffold.
  - A follow-up iteration with `skill-iterate` once they've lived with the v1 for a bit.

## What NOT to do

- **Don't introduce a build step.** No Jekyll, no Astro, no Vite, no bundler. The file the author edits is the file the reader views. One tradeoff this accepts: content lives in HTML, not markdown. That's fine for a concept site — the volume is low and the HTML is obvious.
- **Don't write before intake.** Generic filler ("In today's fast-paced world…") is the signal that intake was skipped.
- **Don't pad with optional pages** (Foundations, Deep-dives, Scale) unless the user has material for them. A tight 3-section site is better than a bloated 8-section site full of hedges.
- **Don't invent pillars or waves.** If you need N pillars and the intake gave you 2, ask for a third rather than confecting one.
- **Don't copy the reference site's specific content** (AI-SDLC, RPI, nopCommerce). Copy its **structure** and **voice** — the content must come from the user's intake.
- **Don't load content dynamically via `fetch`.** Inline it in the HTML. `file://` breaks `fetch`, PDF capture becomes harder, and the whole zero-build promise depends on one file working standalone.

## Iteration

This skill is a strong candidate for `skill-iterate`. After a v1 site exists, run `skill-iterate` with a probe task like "create a concept website for <different concept, with full intake material attached>" and tune the skill's files based on friction the probe surfaces. Typical iteration targets:

- Intake prompts that don't elicit enough material.
- Section templates that produce hedged prose.
- Voice guidance that isn't specific enough to reproduce the reference site's feel.
- The generated `index.html` being too long to read / edit comfortably — if this surfaces, consider splitting long sections into companion HTML pages (like the reference's `sdlc-map.html`).
