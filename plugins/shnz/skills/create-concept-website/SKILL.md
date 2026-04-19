---
name: create-concept-website
description: "Scaffold and author a static single-page HTML concept website that explains a concept top-down (Vision = why / art of the possible) and bottom-up (Roadmap = how / waves of tactical adoption; Map = the layers or stages of the concept). Use when the user says 'create a concept website', 'concept site for X', 'vision + roadmap site', 'explainer site for [concept]', 'get everyone on the same page about [concept]', or invokes /create-concept-website. Produces one `index.html` + `assets/style.css` + `assets/script.js` + `data/intake.yml` — zero build step, zero runtime dependencies, opens directly from file://. Includes an arrow-key Present mode and a PDF export path. Modeled on https://stevehoggnz.github.io/ai-sdlc/."
argument-hint: "[target-dir]"
---

<!-- Claude Code adapter — canonical procedure in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

## Claude Code specifics

- **Parse `ARGUMENTS`**: the first token (if present) is the target directory to scaffold into. Default: `./<concept-slug>-site` once the slug is known.
- **Do intake first, scaffold second, write last.** Do not create any files until the user has confirmed: the concept one-liner, the audience, the destination state (vision), and at least a first-pass list of waves (roadmap) and layers (map). Skipping intake produces generic filler that invalidates the whole site.
- **Non-interactive invocation** (e.g. a `skill-iterate` probe, an autonomous agent run, or a run with attached source material and no live user): treat the attached material as confirmed intake and proceed. **Extract** intake fields from the source rather than fabricating them; for any field you had to derive (rather than extract verbatim) flag it in the final summary so the author can confirm later. Still do the intake step — it's now material-extraction rather than user-questioning, but the output shape is the same.
- **Output shape**: one `index.html` containing all nav sections as `<div class="page" id="...">` blocks, plus `assets/style.css`, `assets/script.js`, `data/intake.yml`. No `_layouts/`, no `_config.yml`, no markdown, no Jekyll. Preview = open `index.html` in a browser.
- **Use dedicated tools**:
  - `Write` — creating the initial `index.html`, stylesheet, and script from the scaffold templates.
  - `Edit` — filling the `<div class="page">` section bodies in the write phase (keeps diffs small and preserves surrounding structure).
  - `Bash` — creating directories (`mkdir -p`), opening the file for preview (`open index.html` on macOS), or starting a throwaway static server (`python3 -m http.server`).
  - `Glob` — finding existing content in the repo when the user points at source material.
- **Reference files**, read as needed:
  - [reference/intake.md](./reference/intake.md) — the intake questionnaire + canonical `data/intake.yml` schema.
  - [reference/page-vision.md](./reference/page-vision.md) — Vision section structure + HTML template.
  - [reference/page-roadmap.md](./reference/page-roadmap.md) — Roadmap section structure + HTML template.
  - [reference/page-map.md](./reference/page-map.md) — Map section structure + HTML template.
  - [reference/voice.md](./reference/voice.md) — voice, visual language, metaphor patterns.
  - [reference/scaffold.md](./reference/scaffold.md) — full `index.html` shell + `assets/style.css` + `assets/script.js`.
  - [reference/diagrams.md](./reference/diagrams.md) — themed Mermaid (lazy-loaded) + SVG drop-in escape hatch + anti-slop rules.
  - [reference/slide-mode.md](./reference/slide-mode.md) — arrow-key "Present" mode design notes + customisation points.
  - [reference/pdf-export.md](./reference/pdf-export.md) — print CSS baseline + optional Puppeteer build script for a downloadable `<slug>.pdf`.
- **Never ship placeholder prose.** Every section must reflect the user's actual concept; if you don't have enough material for a section, ask — don't hallucinate a pillar or a wave.
- **Preview before declaring done**: `open <target-dir>/index.html` (macOS) or visit `http://localhost:8000/` after `python3 -m http.server 8000 --directory <target-dir>`. The site works from `file://`; there is no build step, no Ruby, no Node required to view it.

## Typical first interaction

1. User says "create a concept website for X" or `/create-concept-website`.
2. Run the intake questionnaire (see [reference/intake.md](./reference/intake.md)) and get the user to confirm answers.
3. Draft one-line summaries for Vision, Roadmap, Map (and any optional companion pages) and get agreement before writing.
4. Scaffold the site in the target dir (see [reference/scaffold.md](./reference/scaffold.md)) — `index.html` + `assets/{style.css,script.js}` + `data/intake.yml`.
5. Fill the three `<div class="page">` bodies using the section templates + voice guide.
6. Open `index.html`; click through tabs; try Present mode and Cmd+P; iterate with the user.
