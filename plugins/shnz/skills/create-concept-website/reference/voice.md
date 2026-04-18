# Voice & visual language

The reference site ([stevehoggnz.github.io/ai-sdlc](https://stevehoggnz.github.io/ai-sdlc/)) has a specific feel that does a lot of work. It reads as confident, opinionated, and concrete — three properties that most concept sites fail at. This file captures the patterns that produce that feel so they can be reproduced consistently.

## Voice

### Opinionated, not neutral

The site declares the shift ("from humans writing every line to agents executing against intent definitions") rather than surveying possibilities ("there are several perspectives on where AI fits in the SDLC"). Concept sites exist to move the reader to a specific position; neutral copy produces polite indifference.

### Concrete, not abstract

Every claim is paired with a specific example, tool, or incident. "200k lines of code compressed into a 2k-line research brief" beats "efficient context compression". If a sentence could be dropped into an article about a different concept, rewrite it or cut it.

### Short strong metaphors, reused

Pick **1–3 metaphors** from intake and reuse them throughout the site. The reference site's set: "execution is cheap, clarity is expensive" (economic metaphor), "Physics over Law" (constraints over policy), "Dense Handoff Artefacts" (artefacts as communication). Each appears in Vision, recurs in deep-dives, and is load-bearing in at least one explanation.

Do **not** mix more than 3 metaphors across a site. Readers can hold 3; 6 feels incoherent.

### Second person for reader, not first-person plural

"Your journey" is fine. "We believe", "we think" centres the author and is weak. When the author needs to appear, name them once (bio link) rather than lacing "we"s through the copy.

### Cadence

Mix paragraph-length sentences with short punches. The reference site does this: a narrative sentence, a single-sentence follow-up, a bulleted list, a callout. Walls of prose are skimmed; walls of bullets are read as slides.

## Visual language

### Horizontal tab nav

Top of every page — but since the site is single-page, "tab nav" switches which `<div class="page">` is visible, not which URL is loaded. Order matches reading order: Vision → Roadmap → (deep-dives) → Map. Active tab styled distinctly with the accent colour + subtle shadow. The nav itself is part of the site's voice — it's the table of contents for the concept.

### Callouts

Pullquotes (`<blockquote>`) for the "from X to Y" shift and for wave outcomes. Styled with a left accent-border + lightly-tinted surface fill. Used sparingly — at most 1–2 per section — so they stay strong.

If a section has two pullquotes (e.g. the Vision's hero lede at the top and the "from X to Y" shift later), **vary emphasis inside the quote** — bold the X/Y terms in the shift — so they don't visually collide.

### Checklists

Unchecked boxes on the Roadmap. The CSS class `ul.checklist` renders each `<li>` with a `☐` prefix + a divider line — the checkbox look without real `<input>` elements. No JS persistence: the visual of a half-full checklist is the point, even transient. Don't fake interactivity with real inputs unless you're persisting state somewhere (you won't be).

### Badges

Readiness tiers on the Map (Ready / Emerging / Preview). Use color **with** text, not color alone (accessibility). The reference's palette: green for Ready, amber for Emerging, grey for Preview. In print CSS, badges fall back to outlined boxes with `✓` / `~` / `·` prefixes.

### Diagrams

For the Map's "at a glance", a simple HTML card grid (`<div class="cards">`) is usually clearer than a diagram and renders with zero extra dependencies. **Do not reach for mermaid by default** — it doesn't render in plain HTML without adding `mermaid.js` from a CDN. If the concept really needs a diagram, add the CDN script or use an SVG; mention in the PR that you've added a runtime dep.

### Tables

Use tables for: comparison (old-way vs new-way), symmetric enumeration (layer | purpose | readiness), and cheat sheets. Don't force a narrative into a table. Table headers use uppercase small caps via the default stylesheet — keep them short.

### Typography

Inter as primary, with a system-font fallback stack. One accent color + one secondary (the stylesheet uses purple + teal). Generous line-height (1.5–1.7) — concept sites are *read*, not scanned. Body text 16px; `clamp()` on `<h1>` scales it responsively.

## Component vocabulary

The stylesheet ships a set of rich components beyond plain paragraphs and tables. Reach for the right one — plain markup reads as undifferentiated docs, but the wrong rich component reads as design-for-its-own-sake. Rule of thumb: the component should be the *most restrained* shape that carries the intent.

| Component | Use when… | Avoid when… |
|---|---|---|
| `<p class="eyebrow">` | You want the reader oriented before the `<h2>` ("THE DESTINATION", "STAGE 1 OUTCOME"). Works as a category marker that reappears throughout the site. | The heading already carries its role clearly. Don't label every `<h2>` — it becomes noise. |
| `<blockquote>` | A signature single-sentence statement you want the reader to repeat ("From X to Y"). Also: the moment-it-clicks story. | Summarising. Use a paragraph. |
| `<span class="hl-*">` | Drawing the eye through a dense story where 2–3 terms carry the emotional weight ("`compiler refuses to build`"). | Decorating random emphasis. Bold (`<strong>`) is for *structural* emphasis; highlights are for *dramatic* emphasis. |
| `.flow` / `.flow-row` | Narrating an A→B→C→… sequence where each step has an actor and an action (ticket flow, pipeline, user journey). | Listing unordered items. Use `<ul>` or `.cards`. Also: don't use .flow for 2 items — the component is meant to show *progression*. |
| `.pillar-grid` / `.pillar` | 3 (or 4) named principles that the concept rests on. Each has an icon, a short name, a body. | Listing 5+ items. At that point it's a `.cards` grid, not pillars. Pillars read as "the big ideas"; more than 4 dilutes that. |
| `.journey` / `.journey-card` | 3–5 maturity stages / role progressions where each has a name and a signal. | A linear ordered list of tasks. That's the Roadmap. Journey is *where you are*, not *what you do next*. |
| `.path` / `.path-tile` | Wayfinding: small icon tiles pointing to other sections / tabs. | Primary content. The path row is connective tissue, not a destination. |
| `.timeline` | Roadmap header only — shows the shape of the whole journey before the reader drills in. | Any non-Roadmap context. The timeline + wave markers together are specifically the Roadmap's visual signature; reusing them elsewhere weakens both. |
| `<section class="wave">` | Roadmap waves. Each is one slide in present mode. | Any other context. See above. |
| `.resources` / `.resource` | Learning-resource link lists with a categorised source tag (GH Skill, MS Learn, etc.). Use a **consistent `.resource-source` color per source platform across the whole site** (e.g. GH Skill always teal, MS Learn always blue). Pills are for *scanning*: consistent colors let the reader filter at a glance. | Inline links in prose. Pills are for a curated list; inline links stay inline. Don't rotate source-tag colors within a wave — breaks the scan-by-platform affordance. |
| `.outcome` | End-of-wave success-criteria callout. | Regular paragraphs. Overusing outcome callouts dilutes the "this is the bar for done" signal. |
| `<table>` | Symmetric enumeration where every row shares the same columns (layer | purpose | readiness). | A narrative with a sequence. Use `.flow`. |
| `.cards` | Map's "at a glance" grid; generic 3–6 item hub cards. | Anything that has structure beyond "title + one-liner". Pillars → `.pillar-grid`. Journey → `.journey`. |
| `.badge` / `.badge-ready/emerging/preview` | Map readiness markers; inline with a heading. | Decorative labels. Badges signal *state*, not category. Category = eyebrow or pill. |

### Emoji

Sparingly. One emoji per major section heading, used as a category marker (🧭 for navigation / orientation, 🛠️ for tools, 🎯 for outcomes). Don't emoji inside sentences; don't repeat the same emoji in one page.

## Common failure modes to avoid

- **Executive-deck voice** — "enabling synergies across the value chain". Rewrite as concretely as possible, or cut.
- **Manifesto voice** — long paragraphs of should-statements with no concrete example. Anchor every claim in an artefact.
- **Documentation voice** — reference-y, passive, optionless. Fine for a docs site; wrong for a concept site. Concept sites have a point of view.
- **Slide-deck voice** — bullet-only, no connective tissue. Works for 10 minutes in a room, fails when read cold.

## The test for voice

Read each page aloud. If any sentence:

- could appear in an article about a different concept — rewrite with specifics.
- hedges (mostly, largely, various, several, can often) — pick a side or cut.
- starts with "In today's…" — cut; start with the specific claim.
- names a problem without a stance — add the stance.

A concept site where every sentence passes this test feels different from one where most don't. That difference is the whole product.
