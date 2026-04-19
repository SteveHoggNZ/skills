# PDF export

The site should be downloadable as a PDF. Two approaches ship by default:

| Approach | When to use | Install cost |
|----------|-------------|--------------|
| **Print CSS (browser Cmd+P → Save as PDF)** | Occasional export; reader does it themselves | None |
| **Puppeteer build script (`npm run pdf`)** | Site owner wants a ready-to-download `site.pdf` linked in nav | One dev dep (`puppeteer`) |

Ship the **print CSS baseline always** (it's already in `assets/style.css` per [scaffold.md](./scaffold.md)). Add the Puppeteer script only when the user wants a one-click downloadable.

## Why not html-to-image + jsPDF (the React-app style)

Some React apps rasterise the DOM to JPEG via `html-to-image` + slice with `jsPDF`. That's the right call for WebGL / MapLibre / React Flow content where CSS paged-media rules don't capture the full picture.

A concept site has none of that. It's server-rendered HTML + CSS + a small vanilla JS. Browsers (and Puppeteer, which is Chrome) already know how to paginate HTML into PDF via the `@media print` rules in our stylesheet. The result is:

- **Selectable / searchable text** (vector, not raster).
- **Small file size** (50KB–500KB for a concept site, vs. several MB raster).
- **Zero JS runtime** for the print-CSS path; one dev dep for Puppeteer.

## Print CSS (always on)

Already shipped in `assets/style.css` per [scaffold.md](./scaffold.md) §`assets/style.css`, inside the `@media print { … }` block. Notable behaviours:

- Every `<div class="page">` starts on a new sheet — so the PDF has Vision → Roadmap → Map sections one after the other, regardless of which tab was active when the user hit Cmd+P.
- Chrome (header, footer, skip-link, present button, slide counter) is hidden.
- The purple/teal dark theme reverts to black-on-white.
- Readiness badges render as outlined boxes with `✓` / `~` / `·` prefixes instead of solid colours (no-coloured-ink fallback).
- External link URLs print in parentheses after the link text (`[link text] (https://…)`).

Tell the user: **Cmd+P (or Ctrl+P) → Save as PDF**. Works in any browser, no install, no build step.

## Puppeteer build script (opt-in)

For a one-click downloadable PDF linked from the nav (`[Download PDF ↓]`), add a Node script. Since the site is a single `index.html` with all sections already in the DOM, the script is simple — no multi-page crawl, no tab navigation, no concatenation. Just load the file, switch to print media, and save.

### `package.json`

```json
{
  "name": "{{concept-slug}}-site",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "pdf": "node scripts/build-pdf.mjs"
  },
  "devDependencies": {
    "puppeteer": "^23.0.0"
  }
}
```

### `scripts/build-pdf.mjs`

```js
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');

// The print CSS makes every <div class="page"> display — regardless of
// which tab is "active". So we just load the file and print.
const indexPath = resolve(root, 'index.html');
const outDir = resolve(root, 'assets');
const slug = process.env.SLUG || 'site';
const outFile = resolve(outDir, `${slug}.pdf`);

const browser = await puppeteer.launch();
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(indexPath).toString(), { waitUntil: 'networkidle0' });

  // Wait for any lazy-loaded Mermaid diagrams to render before capture.
  // mermaid adds `data-processed="true"` to each <pre class="mermaid"> once done.
  await page.evaluate(async () => {
    const pending = () =>
      document.querySelectorAll('.mermaid:not([data-processed="true"])').length;
    if (pending() === 0) return;
    // Poll for up to 5 seconds; the render is fast on A4.
    const deadline = Date.now() + 5000;
    while (pending() > 0 && Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 100));
    }
  });

  await page.emulateMediaType('print');

  mkdirSync(outDir, { recursive: true });
  await page.pdf({
    path: outFile,
    format: 'A4',
    printBackground: true,
    margin: { top: '18mm', right: '16mm', bottom: '18mm', left: '16mm' },
  });
  console.log(`Wrote ${outFile}`);
} finally {
  await browser.close();
}
```

Set `SLUG` via env var, or hard-code it in the script, or read it from `data/intake.yml` (see below for a yaml-reading variant).

### Linking from nav

Once `assets/<slug>.pdf` exists, add a link next to the Present button in `index.html`:

```html
<a class="pdf-link" href="assets/{{slug}}.pdf" download>PDF ↓</a>
```

And style it to sit beside `.present-toggle`:

```css
.pdf-link {
  padding: 8px 14px; border: none;
  font-size: 0.85rem; font-weight: 500;
  color: var(--text-muted); background: transparent;
  border-radius: 8px; text-decoration: none;
  transition: var(--transition);
}
.pdf-link:hover { color: var(--text); background: var(--surface-2); }
```

Keep the link hidden until the PDF is built; otherwise readers click a 404:

```js
// In script.js, optional bootstrap:
fetch('assets/{{slug}}.pdf', { method: 'HEAD' })
  .then((r) => { if (r.ok) document.querySelector('.pdf-link')?.removeAttribute('hidden'); })
  .catch(() => {});
```

(Add `hidden` to the `<a>` attribute in the HTML and remove it via this check.)

### When to run

- **Manually before publishing** — `npm run pdf` whenever the site changes.
- **GitHub Actions** — rebuild the PDF on merge to `main` and commit `assets/<slug>.pdf`:

```yaml
# .github/workflows/pdf.yml
name: Build PDF
on:
  push:
    branches: [main]
    paths-ignore: ['assets/*.pdf']
jobs:
  pdf:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run pdf
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: 'chore: rebuild PDF'
          file_pattern: 'assets/*.pdf'
```

- **Skip automation** — tell readers to use Cmd+P. Perfectly fine for low-traffic concept sites.

## Using `data/intake.yml` to pick the filename

If you'd like the PDF filename to track the intake slug automatically:

```js
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';  // add to devDependencies

const intake = yaml.load(readFileSync(resolve(root, 'data/intake.yml'), 'utf8'));
const slug = intake.concept_slug || 'site';
```

## What NOT to do

- **Don't bolt on a client-side PDF button (`html2pdf.js` et al.).** It ships a big JS dep to every visit for a feature most readers won't use. The server-side Puppeteer path generates a better PDF once and ships a cheap `<a>` link.
- **Don't include the generated PDF in Git LFS** unless the site is image-heavy. A 100KB–1MB concept-site PDF is fine in regular Git.
- **Don't try to hand-craft `@page` running headers, generated page numbers, or bookmarks in v1.** The print CSS + Puppeteer baseline is already good enough for stakeholder distribution. Refinements can come from a `skill-iterate` pass if surfaced.
- **Don't regenerate the PDF on every pull request** — only on merge to main (see the Actions workflow). PR previews don't need fresh PDFs.
- **Don't rely on the live site URL in the build script** when the HTML + PDF ship in the same repo. `file://` is deterministic and doesn't need a running server.
