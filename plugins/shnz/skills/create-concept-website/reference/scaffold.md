# Scaffold

A single-page HTML site. Zero build step. Zero runtime dependencies. Opens directly from `file://` or any static server.

## Directory to create

```
<target-dir>/
├── index.html            # the whole site
├── assets/
│   ├── style.css         # base + slide-mode + print CSS
│   └── script.js         # tab switching + present mode
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
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
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

- `meta name="robots" content="noindex"` is a safe default for concept sites (often internal/work-in-progress). Remove when the site is ready for public indexing.
- The Inter Google Font is declared at the shell level because it's a load-bearing part of the reference-site aesthetic. System-font fallback is in the CSS.
- The `<button class="present-toggle">` lives inside the tab-nav so it appears at the far right. `script.js` wires its click handler.

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
  --gradient-text: linear-gradient(135deg, #9b7fff 0%, #00d4aa 100%);
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  --font: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
  background: var(--gradient-text); -webkit-background-clip: text; color: transparent;
  letter-spacing: -0.02em;
}
.tab-nav {
  display: flex; gap: 2px;
  background: var(--surface); border-radius: 10px; padding: 3px;
}
.tab-btn, .present-toggle {
  padding: 8px 18px; border: none; background: transparent; color: var(--text-muted);
  font: inherit; font-size: 0.85rem; font-weight: 500; border-radius: 8px;
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
}
h1 .gradient {
  background: var(--gradient-text); -webkit-background-clip: text; color: transparent;
}
h2 {
  font-size: 1.5rem; font-weight: 700;
  margin: 3rem 0 1rem; letter-spacing: -0.01em;
}
h3 { font-size: 1.15rem; font-weight: 600; margin: 2rem 0 0.75rem; }
p { margin: 1rem 0; color: var(--text); }
p.lede { font-size: 1.15rem; color: var(--text-muted); margin-top: 0; }

/* Pullquote / callout */
blockquote {
  margin: 1.5rem 0; padding: 1rem 1.25rem;
  border-left: 3px solid var(--accent);
  background: var(--surface);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 1.05rem; color: var(--text);
}
blockquote strong { color: var(--accent-light); }

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
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 600; font-size: 0.9rem;
  color: var(--accent); white-space: nowrap;
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
.flow-row.is-teal   .flow-badge { border-left-color: var(--accent-2);     color: var(--accent-2); }
.flow-row.is-blue   .flow-badge { border-left-color: var(--blue);         color: var(--blue); }
.flow-row.is-purple .flow-badge { border-left-color: var(--accent-light); color: var(--accent-light); }
.flow-row.is-orange .flow-badge { border-left-color: var(--orange);       color: var(--orange); }
.flow-row.is-pink   .flow-badge { border-left-color: var(--accent-3);     color: var(--accent-3); }

/* Pillar grid — icon tile + colored top-border + body.
   Usage:
     <div class="pillar-grid">
       <article class="pillar is-orange">
         <div class="pillar-icon">🎯</div>
         <h3>Intent Engineering</h3>
         <p>Communicate goals and constraints…</p>
       </article>
     </div> */
.pillar-grid {
  display: grid; gap: 1rem; margin: 2rem 0;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}
.pillar {
  padding: 1.25rem 1.5rem 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 2px solid var(--accent);
  border-radius: var(--radius);
}
.pillar-icon {
  width: 36px; height: 36px;
  display: grid; place-items: center;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 1.15rem; margin-bottom: 1rem;
}
.pillar h3 { margin: 0 0 0.5rem; font-size: 1.05rem; }
.pillar p  { margin: 0; color: var(--text-muted); font-size: 0.93rem; line-height: 1.55; }
.pillar.is-teal   { border-top-color: var(--accent-2); }
.pillar.is-orange { border-top-color: var(--orange); }
.pillar.is-pink   { border-top-color: var(--accent-3); }
.pillar.is-blue   { border-top-color: var(--blue); }
.pillar.is-purple { border-top-color: var(--accent-light); }

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
.timeline-bar {
  grid-column: 1 / -1;
  height: 6px; border-radius: 999px;
  background: linear-gradient(90deg,
    var(--accent-2) 0%,
    var(--blue) 25%,
    var(--accent-light) 50%,
    var(--orange) 75%,
    var(--accent-3) 100%);
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
.wave h2 { font-size: 1.5rem; margin-top: 0.25rem; }
.wave.is-teal   h2 { color: var(--accent-2); }
.wave.is-blue   h2 { color: var(--blue); }
.wave.is-purple h2 { color: var(--accent-light); }
.wave.is-orange h2 { color: var(--orange); }
.wave.is-pink   h2 { color: var(--accent-3); }
.wave.is-yellow h2 { color: var(--yellow); }

.wave-tag {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  border-radius: 999px;
  background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.wave.is-teal   .wave-tag { color: var(--accent-2);     border-color: var(--accent-2); }
.wave.is-blue   .wave-tag { color: var(--blue);         border-color: var(--blue); }
.wave.is-purple .wave-tag { color: var(--accent-light); border-color: var(--accent-light); }
.wave.is-orange .wave-tag { color: var(--orange);       border-color: var(--orange); }
.wave.is-pink   .wave-tag { color: var(--accent-3);     border-color: var(--accent-3); }
.wave.is-yellow .wave-tag { color: var(--yellow);       border-color: var(--yellow); }

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
  border-left: 3px solid var(--accent);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.outcome .eyebrow { margin: 0 0 0.25rem; }
.outcome p:last-child { margin: 0; font-size: 0.95rem; }
.wave.is-teal   .outcome { border-left-color: var(--accent-2); }
.wave.is-blue   .outcome { border-left-color: var(--blue); }
.wave.is-purple .outcome { border-left-color: var(--accent-light); }
.wave.is-orange .outcome { border-left-color: var(--orange); }
.wave.is-pink   .outcome { border-left-color: var(--accent-3); }

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
  h1 .gradient { color: #000; background: none; -webkit-text-fill-color: #000; }
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
    <span class="hero-badge">{{category or status}}</span>
    <h1>{{concept title}} <span class="gradient">{{highlight}}</span></h1>
    <p class="lede">{{one-liner}}</p>
  </section>

  <div class="cards">
    <a class="card" href="#vision"  onclick="document.querySelector('[data-page=vision]').click(); return false;">
      <h3>Vision →</h3>
      <p>{{one-line about the why}}</p>
    </a>
    <a class="card" href="#roadmap" onclick="document.querySelector('[data-page=roadmap]').click(); return false;">
      <h3>Roadmap →</h3>
      <p>{{one-line about the how}}</p>
    </a>
    <a class="card" href="#map"     onclick="document.querySelector('[data-page=map]').click(); return false;">
      <h3>Map →</h3>
      <p>{{one-line about the what}}</p>
    </a>
  </div>
</div>
```

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
