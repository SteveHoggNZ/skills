# Create Concept Website (Codex adapter)

When the user asks to create a concept website, vision/roadmap site, or explainer site for a concept, follow the procedure in [core.md](./core.md).

## Codex specifics

- **Parse `ARGUMENTS`** — first token (if present) is the target directory; default is `./<concept-slug>-site` once the slug is known.
- **Do intake first, scaffold second, write last.** See [reference/intake.md](./reference/intake.md). Stop and ask if any of the three load-bearing sections (Vision, Roadmap, Map) lacks material. For non-interactive runs, extract from attached source and flag derived-vs-extracted fields in the final summary.
- **Output shape**: one `index.html` with all nav sections as `<div class="page" id="...">` blocks, plus `assets/style.css`, `assets/script.js`, `data/intake.yml`. Zero build step, zero runtime deps.
- Use shell + file-editing tools for authoring HTML. Use `mkdir -p` for scaffolding. Preview with `open index.html` (macOS) or `python3 -m http.server 8000 --directory <target-dir>`.
- Reference material:
  - [reference/intake.md](./reference/intake.md) — questionnaire + canonical `data/intake.yml` schema.
  - [reference/page-vision.md](./reference/page-vision.md), [reference/page-roadmap.md](./reference/page-roadmap.md), [reference/page-map.md](./reference/page-map.md) — HTML section templates.
  - [reference/voice.md](./reference/voice.md) — voice + visual language.
  - [reference/scaffold.md](./reference/scaffold.md) — `index.html` shell + `assets/style.css` + `assets/script.js`.
  - [reference/slide-mode.md](./reference/slide-mode.md) — arrow-key "Present" mode design notes.
  - [reference/pdf-export.md](./reference/pdf-export.md) — print CSS baseline + optional Puppeteer build script.
- **Never ship placeholder prose.** If you don't have enough material for a section, ask — don't hallucinate pillars or waves.
