# Voice & visual language

The reference site ([stevehoggnz.github.io/ai-sdlc](https://stevehoggnz.github.io/ai-sdlc/)) has a specific feel. It reads as confident, opinionated, and concrete. Those are three properties most concept sites fail at. This file captures the patterns that produce that feel.

It also captures the patterns to avoid. AI-generated concept sites have a recognisable signature (the "vibe-coded" look): purple-to-teal gradients, Inter, bento cards with one-sided colored borders, emoji-as-icons, em-dash overuse, "Transform your X" heroes. The skill's defaults have been tuned against that signature. When you diverge from a default, check that you have a concrete reason rather than a reflex.

## Voice

### Opinionated, not neutral

The site declares a position rather than surveying possibilities. "From humans writing every line to agents executing against intent" beats "there are several perspectives on where AI fits in the SDLC". Concept sites exist to move the reader to a specific position; neutral copy produces polite indifference.

### Concrete, not abstract

Every claim is paired with a specific example, tool, or incident. "200k lines of code compressed into a 2k-line research brief" beats "efficient context compression". If a sentence could be dropped into an article about a different concept, rewrite it or cut it.

### Short strong metaphors, reused

Pick 1–3 metaphors from intake and reuse them throughout the site. The reference set: "execution is cheap, clarity is expensive", "physics over law", "dense handoff artefacts". Each appears in Vision, recurs in deep sections, and is load-bearing in at least one explanation. Do not mix more than 3 metaphors across a site. Readers can hold three; six feels incoherent.

### Second person for reader, not first-person plural

"Your journey" is fine. "We believe", "we think" centres the author and is weak. When the author needs to appear, name them once (bio link) rather than lacing "we"s through the copy.

### Cadence

Mix paragraph-length sentences with short punches. A narrative sentence, a single-sentence follow-up, a bulleted list, a callout. Walls of prose are skimmed; walls of bullets are read as slides.

### Em dashes

At most one em dash (`—`) per load-bearing section body (Vision / Roadmap / Map), and only where a comma, semicolon, colon, or period would genuinely read worse. The AI-slop signal is em-dashes as a default break. In practice this means: when you reach for an em dash, pause. Can you end the sentence and start a new one? Usually yes. Use the period.

Hyphen-minus (-) in compound adjectives is fine ("two-column layout"). Spaced en-dash ( – ) is fine in date ranges. The ban is specifically on `—` as a prose rhythm tic.

### Banned defaults

Do not ship these. They are instant "AI wrote this" signals and they waste the reader's scepticism budget.

Phrases:

- "Transform your [noun]"
- "Unlock your [noun]"
- "Harness the power of…"
- "Seamless"
- "Robust"
- "At the intersection of…"
- "In today's [fast-paced] world…"
- "Elevate your…"
- "It's worth noting that…"
- "Let's delve into…"
- "It's important to note…"
- "Whether you're an X or a Y…"

Visual defaults:

- Purple-to-blue (or purple-to-teal) gradient text in the hero.
- Bento card grid with every card rounded to 12px+, one-sided colored accent border, emoji icon.
- Google Fonts Inter imported at the top of `<head>`.
- Emoji as section icons ("🎯 Intent Engineering", "🚀 Deploy", "📚 Learning Resources").
- "Simple, transparent pricing" / "From zero to hero" subheading patterns.

If you find yourself typing one of these, stop and write the actual thing the concept is doing.

## Visual language

### Horizontal tab nav

Top of every page. Since the site is single-page, the tab nav switches which `<div class="page">` is visible, not which URL is loaded. Order matches reading order: Vision → Roadmap → optional deep sections → Map. Active tab styled with the accent colour. The nav is the table of contents for the concept.

### Callouts (`<blockquote>`)

Distinguished by italic body text, a full subtle border, and slightly tinted surface fill. No one-sided colour stripe. Used sparingly: at most 1–2 per section.

If a section has two pullquotes, vary emphasis inside the quote so they do not collide visually. Bold the X/Y terms in a "from X to Y" shift, for example.

### Checklists

The CSS class `ul.checklist` renders each `<li>` with a `☐` prefix and a divider line. Two-column variant (`ul.checklist.two-col`) is for dense wave checklists where each item sits in its own bordered row. No real `<input type="checkbox">` elements, no JS persistence: the visual of a half-full checklist is the point.

### Badges

Readiness tiers on the Map (Ready / Emerging / Preview). Colour with text, not colour alone. The stylesheet ships green for Ready, amber for Emerging, grey for Preview. In print CSS, badges fall back to outlined boxes with `✓` / `~` / `·` prefixes.

### Cards

Plain surface cards with a full 1px border and a small radius (2px). No one-sided colored top / left border; the category cue is a colored eyebrow label or a colored heading. Do not add "Learn more →" glyphs; card headings are labels, not links-to-nowhere.

### Numbered markers (Roadmap waves)

Circled number plus vertical connector line. Each wave gets one accent colour on the marker and the small wave tag; the heading stays neutral. One colour per wave across `teal → blue → purple → orange → pink` reads as progression without a rainbow bar.

### Diagrams

Diagrams are supported via lazy-loaded themed Mermaid (see [diagrams.md](./diagrams.md) for the full guidance). Any page containing `<pre class="mermaid">` triggers `script.js` to fetch `mermaid@11` from jsDelivr and render with the site's palette; pages without a diagram stay lean.

Reach for a diagram when it carries information the prose can't: a topology, a handoff sequence between many actors, a state machine, a lifecycle loop. Do not reach for one to decorate an already-clear section.

For shapes Mermaid doesn't cover cleanly (maturity pyramid, 2×2 matrix, radial chart, hand-drawn architecture), author an SVG with Excalidraw / tldraw / Figma and drop it in `assets/diagrams/`. See [diagrams.md](./diagrams.md) §"SVG drop-in".

Anti-slop discipline for diagrams:

- Node fills stay neutral. Emphasis is via stroke colour and `classDef`, not rainbow backgrounds.
- No emoji in node labels.
- One diagram per section, at most. Two diagrams in one section means one is padding.
- Every diagram has a `<figcaption>` that names what it shows. Not "Figure 1", an actual sentence.

### Tables

Use tables for: comparison (old-way vs new-way), symmetric enumeration (layer | purpose | readiness), cheat sheets. Do not force a narrative into a table; use `.flow`.

### Typography

Default font stack is the system UI stack (`ui-sans-serif, -apple-system, BlinkMacSystemFont, …`). Inter is intentionally not the default. If a bespoke typeface genuinely fits the concept (editorial / serious / industry-specific), declare it in `:root --font`; do not ship Inter as an aesthetic reflex.

One accent colour plus one secondary (the stylesheet uses purple plus teal). Generous line-height (1.5–1.7). Body text 16px; `clamp()` on `<h1>` scales it responsively.

### No gradients in text

The `.gradient` span has been removed from the stylesheet. Heading colour is a single `var(--text)`. If the concept genuinely needs an emphasis colour on one word, use `<strong>` with a colour variable, not a gradient.

## Component vocabulary

The stylesheet ships a set of rich components. Reach for the right one. Plain markup reads as undifferentiated docs; the wrong rich component reads as design-for-its-own-sake. Rule of thumb: the component should be the *most restrained* shape that carries the intent.

| Component | Use when… | Avoid when… |
|---|---|---|
| `<p class="eyebrow">` | You want the reader oriented before the `<h2>` ("THE DESTINATION", "STAGE 1 OUTCOME"). Works as a category marker that reappears. | The heading already carries its role clearly. Don't label every `<h2>`; it becomes noise. |
| `<blockquote>` | A signature single-sentence statement worth repeating. The moment-it-clicks story. | Summarising. Use a paragraph. |
| `<span class="hl-*">` | Drawing the eye through a dense story where 2–3 terms carry the emotional weight. | Decorating random emphasis. `<strong>` is for structural emphasis; highlights are for dramatic. |
| `.flow` / `.flow-row` | Narrating an A → B → C sequence where each step has an actor and an action. | Listing unordered items. `.flow` with 2 rows is undernourished; raise it to 3+ or use prose. |
| `.pillar-grid` / `.pillar` | 3 (or 4) named principles the concept rests on. Colored heading, neutral card. No top-border stripe, no emoji icon. | 5+ items. That's a `.cards` grid. More than 4 pillars is not pillars. |
| `.journey` / `.journey-card` | 3–5 maturity stages / role progressions with a name and a signal. | A linear ordered list of tasks. That's the Roadmap. |
| `.path` / `.path-tile` | Wayfinding at the end of a section, pointing to other tabs. | Primary content. Connective tissue only. |
| `.timeline` | Roadmap header only. Flat segmented bar, no rainbow. | Any non-Roadmap context. |
| `<section class="wave">` | Roadmap waves. Each is one slide in present mode. | Any other context. |
| `.resources` / `.resource` | Learning-resource link lists with a categorised source tag. Use **one colour per platform across the whole site** (GH Skill always teal, MS Learn always blue, Docs always purple). | Inline links in prose. Rotating source colours within a wave (defeats scan-by-platform). |
| `.outcome` | End-of-wave success-criteria callout. | Regular paragraphs. |
| `<table>` | Symmetric enumeration. | A narrative with a sequence (use `.flow`). |
| `.cards` | Map's "at a glance" grid; generic 3–6 item hub cards. | Pillars (`.pillar-grid`), Journey (`.journey`). |
| `.badge` / `.badge-ready/emerging/preview` | Map readiness markers inline with a heading. | Decorative labels. Badges signal *state*, not category; category is eyebrow or pill. |

### No default emoji

Emoji are not default iconography in this skill. Do not ship `"🎯 Intent Engineering"`, `"🚀 Deploy"`, `"📚 Learning resources"`. The eyebrow label + heading already names the category; the emoji adds nothing and reads as AI-slop.

If the concept has a legitimate iconographic vocabulary, use real SVGs (hand-drawn, Heroicons-style outline, or your existing brand set). Leave the icon slot empty if you do not have real icons. Empty is better than a reflex.

## Common failure modes to avoid

- **Executive-deck voice.** "Enabling synergies across the value chain." Rewrite as concretely as possible, or cut.
- **Manifesto voice.** Long paragraphs of should-statements with no concrete example. Anchor every claim in an artefact.
- **Documentation voice.** Reference-y, passive, optionless. Fine for a docs site; wrong for a concept site. Concept sites have a point of view.
- **Slide-deck voice.** Bullet-only, no connective tissue. Works for 10 minutes in a room, fails when read cold.
- **Generated-site voice.** Every tell in the "Banned defaults" list above. The defaults are banned because they are load-bearing signals that the site was assembled, not written.

## The test for voice

Read each section aloud. If any sentence:

- could appear in an article about a different concept, rewrite with specifics.
- hedges ("mostly", "largely", "various", "several", "can often"), pick a side or cut.
- starts with "In today's…", cut. Start with the specific claim.
- names a problem without a stance, add the stance.
- contains an em dash that a period or colon would replace, replace it.
- contains a phrase from the "Banned defaults" list, rewrite.

A concept site where every sentence passes this test feels different from one where most don't. That difference is the whole product.

## Counterexample: a hero that is not "From X to Y"

The `<blockquote>From X to Y</blockquote>` shape is useful when the shift is genuinely binary. Sometimes it is not. Example of a hero for a concept whose shift is across multiple axes rather than one:

```html
<h1>Platform 2026</h1>
<p class="lede">What running on our infrastructure looks like by end of year.</p>

<p>This is not one shift. It's three: <strong>config as code</strong>
replaces ticketed changes, <strong>SLO budgets</strong> replace outage reviews,
and <strong>paved-road services</strong> replace bespoke stacks. The Roadmap is
ordered against all three. The Map shows where we are on each today.</p>
```

The three bolded terms become the metaphors reused across the rest of the site. No gradient. No pullquote. No "Transform your platform". The concept is stated.
