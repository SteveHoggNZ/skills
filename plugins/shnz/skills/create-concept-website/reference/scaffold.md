# Scaffold

A single-page HTML site. Zero build step. Zero runtime dependencies. Opens directly from `file://` or any static server.

## Directory to create

```
<target-dir>/
├── index.html            # the whole site
├── assets/
│   ├── style.css         # base + diagram + slide-mode + print CSS
│   ├── script.js         # tab switching + present mode + lazy mermaid init
│   └── diagrams/         # (optional) hand-authored SVGs if used (Excalidraw, tldraw, Figma exports)
└── data/
    └── intake.yml        # user's intake answers (see reference/intake.md §Canonical schema)
```

Run:

```bash
mkdir -p <target-dir>/{assets,data}
```

Then write the files below. Section bodies (`<div class="page">` contents) start empty; populate them in the write phase, not the scaffold phase.

## `index.html`

The shell. Replace `{{slug}}`, `{{title}}`, `{{one-liner}}` during scaffold. The three `<div class="page">` blocks stay empty here — they're filled in the write phase using the templates in [page-vision.md](./page-vision.md), [page-roadmap.md](./page-roadmap.md), [page-map.md](./page-map.md).

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>{{title}}</title>
  <meta name="description" content="{{one-liner}}">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <header class="site-header">
    <div class="header-inner">
      <a class="logo" href="#vision">{{title}}</a>
      <nav class="tab-nav" aria-label="Primary">
        <button class="tab-btn" data-page="vision"  aria-current="page">Vision</button>
        <button class="tab-btn" data-page="roadmap">Roadmap</button>
        <button class="tab-btn" data-page="map">Map</button>
        <button class="present-toggle" type="button">Present</button>
      </nav>
    </div>
  </header>

  <main id="main">
    <div class="page active" id="vision">
      <!-- Populated from reference/page-vision.md -->
    </div>
    <div class="page" id="roadmap">
      <!-- Populated from reference/page-roadmap.md -->
    </div>
    <div class="page" id="map">
      <!-- Populated from reference/page-map.md -->
    </div>
  </main>

  <footer class="site-footer">
    <p>{{title}} · <a href="https://github.com/{{user}}/{{repo}}">source</a></p>
  </footer>

  <script src="assets/script.js" defer></script>
</body>
</html>
```

Notes:

- `meta name="robots" content="noindex"` is a safe default for concept sites (often internal / work-in-progress). Remove when the site is ready for public indexing.
- The site uses the system font stack. Do not add a Google Fonts `<link>` in `<head>`; see [voice.md](./voice.md) §"Banned defaults".
- The `<button class="present-toggle">` sits inside the tab-nav so it appears at the far right. `script.js` wires its click handler.
- Mermaid diagrams are supported via lazy-loaded CDN (see [diagrams.md](./diagrams.md)). `script.js` only injects the mermaid bundle if the page contains a `.mermaid` element, so diagram-free sites stay lean.

## `assets/script.js`

Tab switching + present mode in one file. Vanilla JS, no build. ~180 lines.

```js
(() => {
  const qs = (s, el = document) => el.querySelector(s);
  const qsa = (s, el = document) => Array.from(el.querySelectorAll(s));

  const main = qs('#main');
  const tabButtons = qsa('.tab-btn');
  const pages = qsa('.page');

  // ── Tab switching ────────────────────────────────────────────

  function showPage(id) {
    let found = false;
    for (const pg of pages) {
      const match = pg.id === id;
      pg.classList.toggle('active', match);
      if (match) found = true;
    }
    for (const btn of tabButtons) {
      const match = btn.dataset.page === id;
      btn.classList.toggle('active', match);
      if (match) btn.setAttribute('aria-current', 'page');
      else btn.removeAttribute('aria-current');
    }
    if (!found && pages[0]) {
      pages[0].classList.add('active');
      if (tabButtons[0]) {
        tabButtons[0].classList.add('active');
        tabButtons[0].setAttribute('aria-current', 'page');
      }
    }
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
    // Mermaid can only measure a visible container, so render any
    // diagrams on this tab now if they weren't rendered at load time.
    if (window.__renderVisibleDiagrams) window.__renderVisibleDiagrams();
  }

  for (const btn of tabButtons) {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const id = btn.dataset.page;
      history.pushState(null, '', `#${id}`);
      showPage(id);
    });
  }

  window.addEventListener('hashchange', () => {
    const id = window.location.hash.replace(/^#/, '');
    if (id) showPage(id);
  });

  // Initial state from hash, else first page.
  {
    const initial = window.location.hash.replace(/^#/, '');
    if (initial) showPage(initial);
  }

  // ── Present / slide mode ────────────────────────────────────

  // Slides are built from <h2> boundaries across ALL .page divs,
  // in nav order. That lets the user walk the whole site as one deck.

  let slides = [];
  let slideIndex = 0;
  let savedScrollY = 0;
  let savedActiveId = null;

  function buildSlides() {
    // Slides are driven by:
    //  - <h2> boundaries inside a .page (default), AND
    //  - a whole <section class="wave"> is its own slide
    //    (so a numbered roadmap wave presents as one frame).
    const groups = [];
    for (const pg of pages) {
      let current = [];
      const flush = () => {
        if (current.length > 0) { groups.push({ pageId: pg.id, nodes: current }); current = []; }
      };
      for (const child of Array.from(pg.children)) {
        if (child.matches && child.matches('section.wave, .wave')) {
          flush();
          groups.push({ pageId: pg.id, nodes: [child] });
          continue;
        }
        if (child.tagName === 'H2') flush();
        current.push(child);
      }
      flush();
    }
    return groups;
  }

  function enterPresent() {
    slides = buildSlides();
    if (slides.length === 0) return;
    savedScrollY = window.scrollY;
    savedActiveId = (pages.find((p) => p.classList.contains('active')) || pages[0]).id;
    document.body.classList.add('present-mode');

    const hash = window.location.hash.match(/^#slide-(\d+)$/);
    if (hash) slideIndex = Math.max(0, Math.min(slides.length - 1, parseInt(hash[1], 10) - 1));
    else slideIndex = 0;

    renderSlide();
    window.addEventListener('keydown', onKey);
    main.addEventListener('click', onClick);
    syncUrl();
  }

  function exitPresent() {
    document.body.classList.remove('present-mode');

    // Restore original page children from the flat slide list.
    for (const pg of pages) pg.innerHTML = '';
    for (const { pageId, nodes } of slides) {
      const pg = pages.find((p) => p.id === pageId);
      if (!pg) continue;
      for (const n of nodes) pg.appendChild(n);
    }

    window.removeEventListener('keydown', onKey);
    main.removeEventListener('click', onClick);

    const url = new URL(window.location.href);
    url.hash = savedActiveId ? `#${savedActiveId}` : '';
    history.replaceState(null, '', url.toString());

    if (savedActiveId) showPage(savedActiveId);
    window.scrollTo(0, savedScrollY);
  }

  function renderSlide() {
    // Clear every page then rebuild the one containing this slide, with only its nodes.
    for (const pg of pages) pg.innerHTML = '';

    const slide = slides[slideIndex];
    const hostPage = pages.find((p) => p.id === slide.pageId);
    if (!hostPage) return;

    const stage = document.createElement('div');
    stage.className = 'slide-stage';
    for (const n of slide.nodes) stage.appendChild(n);
    hostPage.appendChild(stage);

    // Force the host page to be the only "active" one while in present mode.
    for (const pg of pages) pg.classList.toggle('active', pg.id === slide.pageId);

    let counter = qs('.slide-counter');
    if (!counter) {
      counter = document.createElement('div');
      counter.className = 'slide-counter';
      document.body.appendChild(counter);
    }
    counter.textContent = `${slideIndex + 1} / ${slides.length}  ·  ${slide.pageId}`;

    syncUrl();
  }

  function syncUrl() {
    const url = new URL(window.location.href);
    url.hash = `slide-${slideIndex + 1}`;
    history.replaceState(null, '', url.toString());
  }

  function go(delta) {
    const next = Math.max(0, Math.min(slides.length - 1, slideIndex + delta));
    if (next === slideIndex) return;
    slideIndex = next;
    renderSlide();
  }

  function onKey(e) {
    if (e.key === 'Escape') return exitPresent();
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); return go(1); }
    if (e.key === 'ArrowLeft'  || e.key === 'PageUp')                    { e.preventDefault(); return go(-1); }
    if (e.key === 'Home') { slideIndex = 0; return renderSlide(); }
    if (e.key === 'End')  { slideIndex = slides.length - 1; return renderSlide(); }
  }

  function onClick(e) {
    if (e.target.closest('a, button, input, label, summary, details')) return;
    go(1);
  }

  const toggle = qs('.present-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      if (document.body.classList.contains('present-mode')) exitPresent();
      else enterPresent();
    });
  }

  // Enter via ?present=1
  if (new URLSearchParams(window.location.search).get('present') === '1') enterPresent();

  // ── Mermaid (lazy-loaded) ───────────────────────────────
  // Only inject the CDN bundle if this page has diagrams.
  // Keeps sites without diagrams lean.
  function readVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function mermaidThemeVars() {
    const bg = readVar('--bg');
    const surface = readVar('--surface');
    const surface2 = readVar('--surface-2');
    const text = readVar('--text');
    const textMuted = readVar('--text-muted');
    const border = readVar('--border');
    return {
      fontFamily: readVar('--font') || 'ui-sans-serif, -apple-system, sans-serif',
      fontSize: '14px',
      background: 'transparent',
      primaryColor: surface,
      primaryTextColor: text,
      primaryBorderColor: border,
      secondaryColor: surface2,
      tertiaryColor: surface2,
      lineColor: textMuted,
      textColor: text,
      mainBkg: surface,
      nodeBorder: border,
      clusterBkg: bg,
      clusterBorder: border,
      noteBkgColor: surface2,
      noteTextColor: text,
      noteBorderColor: border,
      edgeLabelBackground: bg,
      actorBkg: surface,
      actorBorder: border,
      actorTextColor: text,
      actorLineColor: textMuted,
      signalColor: text,
      signalTextColor: text,
      labelBoxBkgColor: surface,
      labelBoxBorderColor: border,
      labelTextColor: text,
      sequenceNumberColor: bg,
      stateBkg: surface,
      stateTextColor: text,
    };
  }
  function renderVisibleDiagrams() {
    if (!window.mermaid) return;
    const activePage = pages.find((p) => p.classList.contains('active'));
    if (!activePage) return;
    const pending = activePage.querySelectorAll('.mermaid:not([data-processed="true"])');
    if (pending.length === 0) return;
    window.mermaid.run({ nodes: Array.from(pending) });
  }
  function initMermaid() {
    if (!window.mermaid) return;
    window.mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: mermaidThemeVars(),
      securityLevel: 'strict',
      flowchart: { htmlLabels: false, curve: 'basis' },
      sequence: { mirrorActors: false, showSequenceNumbers: false },
    });
    renderVisibleDiagrams();
  }
  if (document.querySelector('.mermaid')) {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
    s.defer = true;
    s.onload = initMermaid;
    document.head.appendChild(s);
  }
  // Render any pending diagrams when their page becomes visible.
  // Mermaid measures the container at render time; hidden pages would
  // otherwise get a 16×16 SVG on first render.
  window.__renderVisibleDiagrams = renderVisibleDiagrams;
})();
```

## `assets/style.css`

One file. Base → cards/badges/pullquotes → print → slide-mode. Adapt the accent to the concept; the dark-theme + purple/teal default matches the reference site's feel.

```css
:root {
  --bg:        #0a0a0f;
  --surface:   #12121a;
  --surface-2: #1a1a26;
  --surface-3: #22222f;
  --border:    #2a2a3a;
  --text:      #e4e4ef;
  --text-muted:#8888a0;
  --text-dim:  #5a5a72;
  --accent:       #7c5cfc;
  --accent-light: #9b7fff;
  --accent-2:     #00d4aa;
  --accent-3:     #ff6b8a;
  /* Named palette — referenced by component `is-*` variants.
     Keep these stable; many components fail silently if `--blue` /
     `--orange` / `--yellow` resolve to `unset`. */
  --teal:     #00d4aa;
  --blue:     #5b8def;
  --orange:   #e8913a;
  --pink:     #ff6b8a;
  --yellow:   #f0c040;
  --purple:   #9b7fff;
  --ready:    #3bbfa0;
  --emerging: #e8913a;
  --preview:  #8888a0;
  --radius: 2px;
  --radius-sm: 2px;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  /* System font stack. If a bespoke typeface is genuinely warranted for the
     concept (serious editorial, specific industry), declare it here — but
     default to the system so the site doesn't read as "another Inter hero". */
  --font: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  font-size: 16px;
  min-height: 100vh;
  overflow-x: hidden;
}

body::before {
  content: '';
  position: fixed;
  inset: -50%;
  width: 200%; height: 200%;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(124, 92, 252, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(0, 212, 170, 0.04) 0%, transparent 50%);
  z-index: -1;
  pointer-events: none;
}

a { color: var(--accent-light); text-decoration: none; }
a:hover { text-decoration: underline; }

.skip-link { position: absolute; left: -999px; }
.skip-link:focus {
  left: 1rem; top: 1rem;
  background: var(--surface); color: var(--text);
  padding: 0.5rem 0.75rem; border: 1px solid var(--border);
}

/* ── Header ──────────────────────────────────────────── */
.site-header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}
.header-inner {
  max-width: 1100px; margin: 0 auto; padding: 0 2rem;
  display: flex; align-items: center; justify-content: space-between;
  height: 64px; gap: 1.5rem;
}
.logo {
  font-weight: 700; font-size: 1.1rem;
  color: var(--text);
  letter-spacing: -0.02em;
  text-decoration: none;
}
.tab-nav {
  display: flex; gap: 2px;
  background: var(--surface); border-radius: var(--radius-sm); padding: 3px;
}
.tab-btn, .present-toggle {
  padding: 8px 18px; border: none; background: transparent; color: var(--text-muted);
  font: inherit; font-size: 0.85rem; font-weight: 500; border-radius: var(--radius-sm);
  cursor: pointer; transition: var(--transition); white-space: nowrap;
}
.tab-btn:hover, .present-toggle:hover {
  color: var(--text); background: var(--surface-2);
}
.tab-btn.active, .tab-btn[aria-current="page"] {
  color: #fff; background: var(--accent);
  box-shadow: 0 2px 12px rgba(124, 92, 252, 0.3);
}
.present-toggle { margin-left: 0.5rem; border-left: 1px solid var(--border); padding-left: 1rem; }

/* ── Main / Pages ────────────────────────────────────── */
.container, main { max-width: 1100px; margin: 0 auto; padding: 0 2rem; }
.page { display: none; padding: 2.5rem 0 4rem; }
.page.active { display: block; animation: fadeIn 0.4s ease; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

h1 {
  font-size: clamp(2rem, 4vw, 3rem); font-weight: 800;
  line-height: 1.15; letter-spacing: -0.02em;
  margin-bottom: 1rem;
  color: var(--text);
}
h2 {
  font-size: 1.5rem; font-weight: 700;
  margin: 3rem 0 1rem; letter-spacing: -0.01em;
}
h3 { font-size: 1.15rem; font-weight: 600; margin: 2rem 0 0.75rem; }
p { margin: 1rem 0; color: var(--text); }
p.lede { font-size: 1.15rem; color: var(--text-muted); margin-top: 0; }

/* Pullquote / callout. Distinction is via italic + larger size + padding,
   not a one-sided colour stripe. */
blockquote {
  margin: 1.5rem 0; padding: 1rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 1.05rem; font-style: italic; color: var(--text);
}
blockquote p { margin: 0; }
blockquote strong { color: var(--text); font-style: normal; }

/* Tables */
table {
  width: 100%; border-collapse: collapse; margin: 1.5rem 0;
  font-size: 0.95rem;
}
th, td {
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid var(--border);
  text-align: left; vertical-align: top;
}
th { color: var(--text-muted); font-weight: 600; letter-spacing: 0.02em; text-transform: uppercase; font-size: 0.78rem; }

/* Code */
code, pre { font-family: var(--mono); }
code { background: var(--surface); padding: 0.1em 0.35em; border-radius: 4px; font-size: 0.9em; }
pre {
  background: var(--surface); padding: 1rem 1.25rem;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  overflow-x: auto; font-size: 0.9rem; line-height: 1.5;
}
pre code { background: transparent; padding: 0; }

/* Roadmap checklists */
ul.checklist { list-style: none; padding: 0; margin: 1rem 0; }
ul.checklist li {
  position: relative;
  padding: 0.4rem 0 0.4rem 2rem;
  border-bottom: 1px solid var(--border);
}
ul.checklist li::before {
  content: '☐';
  position: absolute; left: 0.4rem; top: 0.4rem;
  color: var(--text-muted); font-size: 1.1rem;
}

/* Readiness badges */
.badge {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  font-size: 0.72rem; font-weight: 600;
  border-radius: 999px;
  color: #fff;
  vertical-align: middle; letter-spacing: 0.03em; text-transform: uppercase;
}
.badge-ready    { background: var(--ready); }
.badge-emerging { background: var(--emerging); }
.badge-preview  { background: var(--preview); }

/* Card grid (used on landing section if present, and for pillars/waves) */
.cards {
  display: grid; gap: 1rem; margin: 2rem 0;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}
.card {
  display: block; padding: 1.25rem 1.5rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text); text-decoration: none;
  transition: var(--transition);
}
.card:hover { border-color: var(--accent); transform: translateY(-2px); text-decoration: none; }
.card h3 { margin: 0 0 0.25rem; font-size: 1.05rem; }
.card p  { margin: 0; color: var(--text-muted); }

/* Hero (optional landing section) */
.hero { padding: 4rem 0 3rem; text-align: center; }
.hero-badge {
  display: inline-block; padding: 6px 16px; border-radius: 20px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--accent-light); font-size: 0.78rem; font-weight: 500;
  margin-bottom: 1.25rem; letter-spacing: 0.04em; text-transform: uppercase;
}

/* Footer */
.site-footer {
  border-top: 1px solid var(--border);
  padding: 1.5rem 2rem;
  text-align: center; color: var(--text-dim);
  font-size: 0.85rem;
}

/* ── Rich components ─────────────────────────────────── */

/* Eyebrow label — small uppercase colored text above h2/h3.
   Usage: <p class="eyebrow">Three pillars</p><h2>What makes this work</h2> */
.eyebrow {
  font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--accent-light);
  margin: 2.5rem 0 0.4rem;
}
.eyebrow + h1, .eyebrow + h2, .eyebrow + h3 { margin-top: 0; }

/* Inline accent highlights — for drawing the eye through dense prose.
   Usage: <span class="hl-pink">compiler refuses to build</span> */
.hl-teal   { color: var(--accent-2);     font-weight: 600; }
.hl-purple { color: var(--accent-light); font-weight: 600; }
.hl-pink   { color: var(--accent-3);     font-weight: 600; }
.hl-orange { color: var(--orange);       font-weight: 600; }
.hl-blue   { color: var(--blue);         font-weight: 600; }
.hl-yellow { color: var(--yellow);       font-weight: 600; }

/* Flow rows — ticket → action narrative.
   Usage:
     <div class="flow">
       <div class="flow-row is-teal">
         <div class="flow-badge">📄 Ticket Created</div>
         <div class="flow-arrow">→</div>
         <div class="flow-body"><strong>Research agent</strong> maps the files, produces research.md</div>
       </div>
     </div>
   Variants: is-teal | is-blue | is-purple | is-orange | is-pink */
.flow { display: flex; flex-direction: column; gap: 0.5rem; margin: 1.5rem 0; }
.flow-row {
  display: grid;
  grid-template-columns: minmax(9rem, 11rem) auto 1fr;
  align-items: stretch; gap: 0.75rem;
}
.flow-badge {
  padding: 0.65rem 0.9rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-weight: 600; font-size: 0.9rem;
  color: var(--text); white-space: nowrap;
  display: flex; align-items: center;
}
.flow-arrow {
  display: flex; align-items: center;
  color: var(--text-dim); font-size: 1.1rem;
}
.flow-body {
  padding: 0.65rem 0.9rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  display: flex; align-items: center;
  font-size: 0.95rem;
}
.flow-body strong { color: var(--text); }
/* Colour distinction lives in text weight and colour; no left stripes. */
.flow-row.is-teal   .flow-badge { color: var(--accent-2); }
.flow-row.is-blue   .flow-badge { color: var(--blue); }
.flow-row.is-purple .flow-badge { color: var(--accent-light); }
.flow-row.is-orange .flow-badge { color: var(--orange); }
.flow-row.is-pink   .flow-badge { color: var(--accent-3); }

/* Pillar grid — subtle-bordered card + bold heading + body.
   Usage:
     <div class="pillar-grid">
       <article class="pillar is-orange">
         <p class="eyebrow">Principle 1</p>
         <h3>Intent Engineering</h3>
         <p>Communicate goals and constraints…</p>
       </article>
     </div>
   The category cue is the colored eyebrow above the heading; the heading
   itself carries the accent color. No one-sided colored stripes.
   (Optional: a leading `<svg class="pillar-icon">` is supported by the rule
   below for authors who want a real icon — do not use emoji as a stand-in.) */
.pillar-grid {
  display: grid; gap: 1rem; margin: 2rem 0;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}
.pillar {
  padding: 1.25rem 1.5rem 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.pillar-icon {
  /* Optional SVG container; authors bring their own icon.
     Do not put emoji here — see voice.md §Banned defaults. */
  width: 28px; height: 28px;
  margin-bottom: 0.75rem;
  color: var(--text-muted);
}
.pillar h3 { margin: 0 0 0.5rem; font-size: 1.05rem; color: var(--text); }
.pillar p  { margin: 0; color: var(--text-muted); font-size: 0.93rem; line-height: 1.55; }
.pillar.is-teal   h3 { color: var(--accent-2); }
.pillar.is-orange h3 { color: var(--orange); }
.pillar.is-pink   h3 { color: var(--accent-3); }
.pillar.is-blue   h3 { color: var(--blue); }
.pillar.is-purple h3 { color: var(--accent-light); }

/* Journey cards — eyebrow + colored role name + body. Usually 3 across.
   Usage:
     <div class="journey">
       <div class="journey-card is-orange">
         <p class="eyebrow">Where you start</p>
         <p class="role">Maker</p>
         <p>You write code. AI suggests lines…</p>
       </div>
     </div> */
.journey {
  display: grid; gap: 0.75rem; margin: 2rem 0;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
}
.journey-card {
  padding: 1.25rem 1.5rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius);
}
.journey-card .eyebrow { margin: 0 0 0.25rem; }
.journey-card .role {
  font-size: 1.2rem; font-weight: 700;
  margin: 0 0 0.75rem; letter-spacing: -0.01em;
}
.journey-card p:last-child { margin: 0; color: var(--text-muted); font-size: 0.92rem; line-height: 1.55; }
.journey-card.is-orange .role { color: var(--orange); }
.journey-card.is-blue   .role { color: var(--blue); }
.journey-card.is-purple .role { color: var(--accent-light); }
.journey-card.is-teal   .role { color: var(--accent-2); }
.journey-card.is-pink   .role { color: var(--accent-3); }

/* Icon-tile path row — "How we get there" with emoji per tab.
   Usage:
     <div class="path">
       <a class="path-tile" href="#roadmap"><span class="path-emoji">🗺️</span><span class="path-label">Roadmap</span><span class="path-note">Your checklist</span></a>
     </div> */
.path {
  display: grid; gap: 0.5rem; margin: 1.5rem 0;
  grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
}
.path-tile {
  display: flex; flex-direction: column; align-items: center; text-align: center;
  padding: 1rem 0.75rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-decoration: none; color: var(--text);
  transition: var(--transition);
}
.path-tile:hover { border-color: var(--accent); transform: translateY(-2px); text-decoration: none; }
.path-emoji { font-size: 1.5rem; margin-bottom: 0.5rem; }
.path-label { font-weight: 600; font-size: 0.95rem; }
.path-label.is-teal   { color: var(--accent-2); }
.path-label.is-blue   { color: var(--blue); }
.path-label.is-purple { color: var(--accent-light); }
.path-label.is-orange { color: var(--orange); }
.path-label.is-pink   { color: var(--accent-3); }
.path-label.is-yellow { color: var(--yellow); }
.path-note  { color: var(--text-dim); font-size: 0.78rem; margin-top: 0.25rem; }

/* Timeline bar — roadmap header.
   Usage:
     <div class="timeline" style="--wave-count: 5">
       <span class="timeline-label is-teal">Foundations</span>
       <span class="timeline-label is-blue">Capture Intent</span>
       …
       <div class="timeline-bar"></div>
     </div>
     <p class="timeline-hint">Tick boxes below to track progress.</p> */
.timeline {
  display: grid;
  grid-template-columns: repeat(var(--wave-count, 5), 1fr);
  row-gap: 0.5rem; column-gap: 0.25rem;
  margin: 1.5rem 0 0.25rem;
}
.timeline-label {
  font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted);
}
.timeline-label.is-teal   { color: var(--accent-2); }
.timeline-label.is-blue   { color: var(--blue); }
.timeline-label.is-purple { color: var(--accent-light); }
.timeline-label.is-orange { color: var(--orange); }
.timeline-label.is-pink   { color: var(--accent-3); }
.timeline-label.is-yellow { color: var(--yellow); }
/* Segmented flat bar — one cell per wave. No gradient. */
.timeline-bar {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(var(--wave-count, 5), 1fr);
  gap: 2px;
  margin-top: 0.25rem;
}
.timeline-bar::before,
.timeline-bar > * {
  /* If author doesn't supply per-step markers, render a single flat bar */
  content: '';
  height: 4px;
  background: var(--border);
  grid-column: 1 / -1;
}
.timeline-hint {
  text-align: center; color: var(--text-muted);
  font-size: 0.85rem; margin: 0.5rem 0 2rem;
}

/* Wave — numbered circle marker + vertical connector line + content.
   Usage (slide-mode treats one .wave as one slide):
     <section class="wave is-teal" data-wave="1">
       <span class="wave-tag">Wave 1 — Assistance</span>
       <h2>Foundations: Learn the Tools</h2>
       <p>intro…</p>
       <ul class="checklist two-col"> … </ul>
       <p class="eyebrow">Learning resources</p>
       <div class="resources"> … </div>
       <div class="outcome"> … </div>
     </section> */
.wave {
  position: relative;
  padding: 0 0 2rem 3.5rem;
  margin-top: 3rem;
}
.wave::before {
  content: attr(data-wave);
  position: absolute; left: 0; top: 0;
  width: 2.5rem; height: 2.5rem;
  border: 2px solid var(--accent);
  background: var(--bg);
  border-radius: 50%;
  display: grid; place-items: center;
  font-weight: 700; font-size: 1.1rem;
  color: var(--accent);
  z-index: 1;
}
.wave::after {
  content: '';
  position: absolute; left: 1.2rem; top: 2.5rem; bottom: -1.5rem;
  width: 2px;
  background: var(--border);
}
.wave:last-of-type::after { display: none; }
.wave.is-teal::before   { border-color: var(--accent-2);     color: var(--accent-2); }
.wave.is-blue::before   { border-color: var(--blue);         color: var(--blue); }
.wave.is-purple::before { border-color: var(--accent-light); color: var(--accent-light); }
.wave.is-orange::before { border-color: var(--orange);       color: var(--orange); }
.wave.is-pink::before   { border-color: var(--accent-3);     color: var(--accent-3); }
.wave.is-yellow::before { border-color: var(--yellow);       color: var(--yellow); }
/* Wave heading stays neutral. The numbered marker carries the accent colour;
   tinting the heading too doubles up on decoration. */
.wave h2 { font-size: 1.5rem; margin-top: 0.25rem; color: var(--text); }

.wave-tag {
  display: inline-block;
  padding: 0.2rem 0.65rem;
  font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  border-radius: var(--radius-sm);
  background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.wave.is-teal   .wave-tag { color: var(--accent-2); }
.wave.is-blue   .wave-tag { color: var(--blue); }
.wave.is-purple .wave-tag { color: var(--accent-light); }
.wave.is-orange .wave-tag { color: var(--orange); }
.wave.is-pink   .wave-tag { color: var(--accent-3); }
.wave.is-yellow .wave-tag { color: var(--yellow); }

/* Checklist — two-column variant for dense wave checklists. */
ul.checklist.two-col {
  display: grid; gap: 0.5rem; list-style: none; padding: 0; margin: 1rem 0;
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
}
ul.checklist.two-col li {
  position: relative; margin: 0;
  padding: 0.7rem 0.9rem 0.7rem 2.3rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.92rem; line-height: 1.5;
}
ul.checklist.two-col li::before {
  content: '☐';
  position: absolute; left: 0.85rem; top: 0.6rem;
  color: var(--text-muted); font-size: 1.1rem;
}
ul.checklist.two-col li strong { color: var(--text); }

/* Resource pills — per-wave learning resources.
   Usage:
     <div class="resources">
       <a class="resource" href="…"><span class="resource-source is-teal">GH Skill</span>Getting Started with GitHub Copilot</a>
     </div> */
.resources { display: flex; flex-direction: column; gap: 0.4rem; margin: 0.75rem 0 1.25rem; }
.resource {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.55rem 0.85rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-decoration: none; color: var(--text);
  font-size: 0.92rem;
  transition: var(--transition);
}
.resource:hover { border-color: var(--accent); text-decoration: none; }
.resource-source {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  font-size: 0.68rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em;
  border-radius: 4px;
  background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text-muted);
  white-space: nowrap;
}
.resource-source.is-teal   { color: var(--accent-2);     border-color: var(--accent-2); }
.resource-source.is-blue   { color: var(--blue);         border-color: var(--blue); }
.resource-source.is-purple { color: var(--accent-light); border-color: var(--accent-light); }
.resource-source.is-orange { color: var(--orange);       border-color: var(--orange); }
.resource-source.is-pink   { color: var(--accent-3);     border-color: var(--accent-3); }

/* Outcome callout — end of each wave.
   Usage:
     <div class="outcome">
       <p class="eyebrow">Stage 1 outcome</p>
       <p>You can use X as a fast, reliable companion…</p>
     </div> */
.outcome {
  margin: 1rem 0;
  padding: 1rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.outcome .eyebrow { margin: 0 0 0.25rem; }
.outcome p:last-child { margin: 0; font-size: 0.95rem; }

/* Diagram wrapper (mermaid or SVG).
   Usage:
     <figure class="diagram">
       <pre class="mermaid">
         flowchart LR
           Plan --> Design --> Code
       </pre>
       <figcaption>What a ticket looks like end to end.</figcaption>
     </figure>
   For a static SVG (Excalidraw / tldraw / hand-authored):
     <figure class="diagram">
       <img src="assets/diagrams/lifecycle.svg" alt="Eight-stage lifecycle …">
       <figcaption>…</figcaption>
     </figure> */
.diagram {
  margin: 2rem 0;
  padding: 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
}
.diagram .mermaid,
.diagram svg,
.diagram img {
  display: block;
  margin: 0 auto;
  max-width: 100%;
  height: auto;
}
.diagram figcaption {
  margin-top: 1rem;
  color: var(--text-muted);
  font-size: 0.88rem;
  text-align: center;
  font-style: italic;
}
/* Pre used for mermaid source shouldn't look like code */
.diagram pre.mermaid {
  background: transparent;
  border: none;
  padding: 0;
  color: var(--text);
  font-family: var(--font);
  white-space: normal;
}

/* ── HTML-native diagram components ──────────────────── */

/* Stack diagram — vertical layered blocks.
   Usage:
     <div class="stack-diagram">
       <div class="stack-layer is-purple"><h4>Intent</h4><p>…</p></div>
       <div class="stack-layer is-blue"><h4>Context</h4><p>…</p></div>
       <div class="stack-layer is-teal"><h4>Prompting</h4><p>…</p></div>
     </div>
   The first layer sits on top and inherits slightly more visual weight. */
.stack-diagram {
  display: flex; flex-direction: column;
  margin: 1.5rem 0;
  border-radius: var(--radius); overflow: hidden;
  border: 1px solid var(--border);
}
.stack-layer {
  padding: 1.1rem 1.4rem;
  background: var(--surface);
  position: relative;
}
.stack-layer + .stack-layer { border-top: 1px solid var(--border); }
.stack-layer:first-child { background: var(--surface-2); }
.stack-layer h4 {
  margin: 0 0 0.2rem; font-size: 1rem; font-weight: 600;
  color: var(--text);
}
.stack-layer p { margin: 0; color: var(--text-muted); font-size: 0.92rem; line-height: 1.5; }
.stack-layer.is-teal   h4 { color: var(--accent-2); }
.stack-layer.is-blue   h4 { color: var(--blue); }
.stack-layer.is-purple h4 { color: var(--accent-light); }
.stack-layer.is-orange h4 { color: var(--orange); }
.stack-layer.is-pink   h4 { color: var(--accent-3); }

/* Chain — horizontal sequence of boxes connected by CSS arrows.
   Usage:
     <div class="chain">
       <div class="chain-step is-teal"><h4>Assistance</h4><p>…</p></div>
       <div class="chain-step is-blue"><h4>Augmentation</h4><p>…</p></div>
       …
     </div>
   Lighter weight than .flow when the narrative is just a named sequence
   without separate actor/action columns. */
.chain {
  display: flex; align-items: stretch;
  margin: 1.5rem 0;
  overflow-x: auto;
  gap: 1.75rem;
  padding: 0.25rem 0.25rem 0.75rem;
}
.chain-step {
  position: relative; flex: 1 1 0;
  min-width: 10rem;
  padding: 0.85rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.chain-step + .chain-step::before {
  content: '';
  position: absolute; left: -1.4rem; top: 50%;
  width: 0.6rem; height: 0.6rem;
  border-top: 2px solid var(--text-muted);
  border-right: 2px solid var(--text-muted);
  transform: translateY(-50%) rotate(45deg);
}
.chain-step h4 { margin: 0 0 0.2rem; font-size: 0.9rem; font-weight: 600; }
.chain-step p  { margin: 0; color: var(--text-muted); font-size: 0.82rem; line-height: 1.5; }
.chain-step.is-teal   h4 { color: var(--accent-2); }
.chain-step.is-blue   h4 { color: var(--blue); }
.chain-step.is-purple h4 { color: var(--accent-light); }
.chain-step.is-orange h4 { color: var(--orange); }
.chain-step.is-pink   h4 { color: var(--accent-3); }

/* Hex grid — hexagonal cells for lifecycle / phase concepts.
   The grid layout is rectangular; the "loop" is carried by the content
   (last cell says "loops back to start"), not the layout itself.
   Usage:
     <div class="hex-grid">
       <div class="hex"><div class="hex-inner"><h4>Plan</h4><p>Intent</p></div></div>
       …
     </div> */
.hex-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 0.5rem;
  margin: 2rem 0;
}
.hex {
  position: relative;
  aspect-ratio: 1.15 / 1;
  background: var(--border);
  clip-path: polygon(25% 0, 75% 0, 100% 50%, 75% 100%, 25% 100%, 0 50%);
}
.hex::before {
  content: '';
  position: absolute; inset: 1px;
  background: var(--surface);
  clip-path: polygon(25% 0, 75% 0, 100% 50%, 75% 100%, 25% 100%, 0 50%);
  z-index: 0;
}
.hex-inner {
  position: relative; z-index: 1;
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center;
  padding: 0.5rem 1rem;
}
.hex-inner h4 { margin: 0 0 0.2rem; font-size: 0.88rem; font-weight: 600; color: var(--text); }
.hex-inner p  { margin: 0; color: var(--text-muted); font-size: 0.78rem; line-height: 1.35; }
.hex.is-teal   { background: var(--accent-2); }
.hex.is-blue   { background: var(--blue); }
.hex.is-purple { background: var(--accent-light); }
.hex.is-orange { background: var(--orange); }
.hex.is-pink   { background: var(--accent-3); }

/* Pyramid — narrowing tiers. Up to 5 tiers; for more use .stack-diagram.
   Usage:
     <div class="pyramid">
       <div class="pyramid-tier"><h4>Architect of Intent</h4></div>
       <div class="pyramid-tier"><h4>Engineering Manager</h4></div>
       <div class="pyramid-tier"><h4>Maker</h4></div>
     </div>
   Narrowest tier is first; widest is last. */
.pyramid {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.3rem; margin: 2rem 0;
}
.pyramid-tier {
  padding: 0.85rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: center;
  width: 100%;
}
.pyramid-tier:nth-child(1) { max-width: 35%; }
.pyramid-tier:nth-child(2) { max-width: 55%; }
.pyramid-tier:nth-child(3) { max-width: 75%; }
.pyramid-tier:nth-child(4) { max-width: 90%; }
.pyramid-tier:nth-child(5) { max-width: 100%; }
.pyramid-tier h4 { margin: 0; font-size: 0.95rem; font-weight: 600; }
.pyramid-tier p  { margin: 0.25rem 0 0; color: var(--text-muted); font-size: 0.85rem; }

/* 2×2 matrix — four quadrants. Axis labels optional.
   Usage (without axes):
     <div class="matrix-2x2">
       <div class="matrix-cell"><p class="eyebrow">High value · low effort</p><h4>Quick wins</h4><p>…</p></div>
       <div class="matrix-cell"><p class="eyebrow">High value · high effort</p><h4>Strategic bets</h4><p>…</p></div>
       <div class="matrix-cell"><p class="eyebrow">Low value · low effort</p><h4>Housekeeping</h4><p>…</p></div>
       <div class="matrix-cell"><p class="eyebrow">Low value · high effort</p><h4>Traps</h4><p>…</p></div>
     </div>
   The eyebrow in each cell names the axis position so the diagram works
   without a dedicated axis-label band. */
.matrix-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin: 2rem 0;
}
.matrix-cell {
  padding: 1.1rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.matrix-cell .eyebrow { margin: 0 0 0.25rem; }
.matrix-cell h4 { margin: 0 0 0.4rem; font-size: 1rem; }
.matrix-cell p  { margin: 0; color: var(--text-muted); font-size: 0.88rem; line-height: 1.55; }

/* ── Print / PDF ─────────────────────────────────────── */
@media print {
  @page { size: A4; margin: 18mm 16mm; }

  :root {
    --bg: #fff; --surface: #fff; --surface-2: #f5f5f5; --surface-3: #f5f5f5;
    --border: #bbb; --text: #000; --text-muted: #333; --text-dim: #555;
    --accent: #000; --accent-light: #000;
  }
  body { background: #fff; color: #000; font-size: 11pt; line-height: 1.45; }
  body::before { display: none; }
  .site-header, .site-footer, .skip-link, .present-toggle, .slide-counter { display: none !important; }

  /* Show every .page when printing — each section starts a new sheet. */
  .page { display: block !important; page-break-before: always; break-before: page; }
  .page:first-of-type { page-break-before: auto; break-before: auto; }

  h1 { font-size: 20pt; page-break-after: avoid; }
  h2 { font-size: 15pt; page-break-after: avoid; margin-top: 18pt; }
  h3 { font-size: 12pt; page-break-after: avoid; }

  blockquote, table, pre, .cards, ul.checklist li,
  .pillar, .journey-card, .flow-row, .resource, .outcome,
  .wave, .path-tile { page-break-inside: avoid; break-inside: avoid; }

  /* Eyebrows stay visible but without color glow */
  .eyebrow { color: #000 !important; }

  /* Highlights collapse to bold dark text in print */
  .hl-teal, .hl-purple, .hl-pink, .hl-orange, .hl-blue, .hl-yellow {
    color: #000 !important; font-weight: 700;
  }

  /* Flow / pillar / journey / wave accent colors flatten to black borders */
  .flow-badge, .flow-body,
  .pillar, .journey-card, .wave-tag, .resource, .resource-source,
  .outcome { background: #fff !important; border-color: #888 !important; color: #000 !important; }
  .flow-badge { border-left-color: #000 !important; color: #000 !important; }
  .pillar { border-top-color: #000 !important; }
  .journey-card .role, .wave h2,
  .path-label, .timeline-label { color: #000 !important; }

  /* Wave numbered marker still useful in print — but drop the glow */
  .wave { padding-left: 3.2rem; }
  .wave::before {
    border-color: #000 !important; color: #000 !important;
    background: #fff !important;
  }
  .wave::after { background: #bbb !important; }

  /* Timeline bar rasterises poorly; replace gradient with flat grey */
  .timeline-bar { background: #bbb !important; }

  /* Diagrams: mermaid renders a dark-theme SVG at page load. For print,
     flip it via CSS filter so it prints as dark-on-light on white paper.
     Imported <img> diagrams are assumed to already be light-themed, so
     they are left alone. */
  .diagram { background: #fff !important; border-color: #888 !important; }
  .diagram svg { filter: invert(1) hue-rotate(180deg); }
  .diagram img { filter: none; }

  /* HTML-native diagrams: flatten accent colours to black text + grey borders. */
  .stack-diagram, .stack-layer,
  .chain, .chain-step,
  .pyramid-tier,
  .matrix-cell {
    background: #fff !important;
    border-color: #888 !important;
    color: #000 !important;
  }
  .stack-layer h4, .chain-step h4, .pyramid-tier h4, .matrix-cell h4 { color: #000 !important; }
  .chain-step + .chain-step::before {
    border-color: #000 !important;
  }
  /* Hexagons: clip-path strokes don't print well; render as bordered boxes. */
  .hex {
    clip-path: none !important;
    background: #fff !important;
    border: 1px solid #888 !important;
    border-radius: 0 !important;
    aspect-ratio: auto !important;
    padding: 0.5rem 0.75rem !important;
  }
  .hex::before { display: none !important; }
  .hex-inner { padding: 0 !important; }

  a { color: #000; text-decoration: underline; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 9pt; color: #444; }

  .badge { color: #000 !important; background: none !important; border: 1px solid #000; padding: 0 0.4em; }
  .badge-ready::before    { content: "✓ "; }
  .badge-emerging::before { content: "~ "; }
  .badge-preview::before  { content: "· "; }
}

/* ── Slide / Present mode ────────────────────────────── */
body.present-mode { overflow: hidden; background: #000; }
body.present-mode .site-header,
body.present-mode .site-footer { display: none; }
body.present-mode body::before { display: none; }
body.present-mode main { max-width: none; padding: 0; margin: 0; }
body.present-mode .page { padding: 0; }
body.present-mode .page.active {
  position: fixed; inset: 0;
  display: grid; place-items: center;
  background: var(--bg);
}
.slide-stage {
  width: min(90vw, 1400px);
  max-height: min(85vh, calc(90vw * 9 / 16));
  overflow-y: auto;
  padding: 3vmin 5vmin;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  font-size: clamp(1rem, 1.6vmin, 1.4rem); line-height: 1.55;
}
.slide-stage h1 { font-size: clamp(1.8rem, 4vmin, 3rem); }
.slide-stage h2 { font-size: clamp(1.4rem, 3vmin, 2.25rem); margin-top: 0; }
.slide-counter {
  position: fixed; bottom: 1rem; right: 1.25rem;
  font-family: var(--mono); font-size: 0.8rem; color: var(--text-muted);
  background: var(--surface); padding: 0.25rem 0.65rem;
  border-radius: 4px; border: 1px solid var(--border);
  z-index: 200;
}
```

## `data/intake.yml`

Populated in the scaffold step using the canonical schema from [reference/intake.md](./reference/intake.md) §"Canonical schema". Example skeleton (trimmed):

```yaml
concept_slug: ai-sdlc
one_liner: "The AI-native software development lifecycle."
audience: "Software teams and engineering leadership."
why_now: "AI is shifting from autocomplete to agents that execute against intent."
core_shift:
  from: "Humans writing every line"
  to:   "Agents executing against intent definitions"
# … full schema continues per reference/intake.md
```

Not read by the site — just retained as a record of source material for future iterations.

## Landing section (optional)

If the user wants a distinct landing section before Vision (e.g., the reference site has a hero with a CTA), add a fourth `<div class="page active" id="home">` as the first page, **make it the default `.active`**, and remove `.active` from the Vision div. Template:

```html
<div class="page active" id="home">
  <section class="hero">
    <h1>{{concept title}}</h1>
    <p class="lede">{{one-liner}}</p>
  </section>

  <div class="cards">
    <a class="card" href="#vision"  onclick="document.querySelector('[data-page=vision]').click(); return false;">
      <h3>Vision</h3>
      <p>{{one-line about the why}}</p>
    </a>
    <a class="card" href="#roadmap" onclick="document.querySelector('[data-page=roadmap]').click(); return false;">
      <h3>Roadmap</h3>
      <p>{{one-line about the how}}</p>
    </a>
    <a class="card" href="#map"     onclick="document.querySelector('[data-page=map]').click(); return false;">
      <h3>Map</h3>
      <p>{{one-line about the what}}</p>
    </a>
  </div>
</div>
```

Notes on the hero:

- No gradient text in the heading. State the concept plainly in one color.
- Skip the `.hero-badge` "CATEGORY" pill unless it carries real information (e.g. "v2.0", "2026 roadmap"). Do not put mood words in it ("COMING SOON", "INTRODUCING").
- The card headings are just labels. Skip right-pointing arrow glyphs ("Vision →") — they are a reflex, not information.

(The inline `onclick` ensures the tab button also flips, not just the hash. A simpler alternative: just use `href="#vision"` and let `hashchange` handle it.)

Default scaffold does **not** include a landing section — Vision is the first tab. Only add one if the user's intake has a specific hook/headline they want to lead with.

## Preview

```bash
open <target-dir>/index.html
```

That's it. No Ruby, no Node, no bundler, no `jekyll serve`. The file works from `file://`.

For a cleaner dev loop (refresh on edit, correct `#hash` routing on first load):

```bash
python3 -m http.server 8000 --directory <target-dir>
# then open http://localhost:8000/
```

Unlike a Jekyll source tree, this is **safe** — the files being served are real HTML, not markdown. No confusion.

## Deployment

Any static host works. No build step, no config.

- **GitHub Pages**: push the target dir contents to a branch (commonly `main` or `gh-pages`), enable Pages, point it at that branch + `/` folder. Live in ~30s.
- **Netlify / Vercel / Cloudflare Pages**: drag-and-drop the folder, or connect the repo and set "no build command, publish directory = `/`".
- **Copy to any web server**: `rsync` the folder. It's static HTML; everything works.

For a GitHub Pages **project site** (`<user>.github.io/<repo>/`), make sure the `index.html` uses **relative paths** (`assets/style.css`, not `/assets/style.css`) — the scaffold above already does this.
