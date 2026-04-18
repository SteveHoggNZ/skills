# Section: Roadmap (the *how*, bottom-up, sequenced)

The Roadmap section is the tactical half of the site. It answers "what do I do on Monday?" Readers scan it looking for concrete actions, not inspiration. Give them checklists — and give each wave a numbered marker + timeline label so the shape of the whole journey is visible at a glance.

## Structure (in order)

1. **Intro** — `<h1>` + `.lede` one-liner.
2. **Timeline bar** — `<div class="timeline">` at the top showing every wave's colored label + a gradient progress bar. The reader can see the full ascent before drilling in.
3. **How to read this** — short `<ul>`: waves are sequential; checklist boxes are visual-only; success criteria gate the next wave.
4. **Where to start** — one sentence pointing to Wave 1 (or wherever the reader should begin).
5. **One `<section class="wave">` per wave.** Each is its own slide in present mode. Contains:
   - `<span class="wave-tag">` — e.g. "Wave 1 — Assistance".
   - `<h2>` — the wave's name.
   - Intro paragraph.
   - `<ul class="checklist two-col">` — 3–8 concrete checkbox items (two-column layout, each item a card).
   - `<p class="eyebrow">Learning resources</p>` + `.resources` list — colored category pill + title per link.
   - `.outcome` callout — `Stage N outcome` eyebrow + one line describing what's true at the end.

## Voice

- **Imperative and concrete.** "Install the `copilot-instructions.md` template", not "Consider establishing coding standards".
- **Testable, not aspirational.** Each checklist item needs a clear yes/no.
- **Resources, not reading lists.** Every cited resource should earn its place — a tool the reader will use, a template they'll copy, a doc they'll reference repeatedly.
- **Own the sequencing.** If wave 3 depends on wave 2, say so. Don't let the reader think they can skip ahead.

## Wave color choice

Use the palette progression `teal → blue → purple → orange → pink` across waves (`is-teal` → `is-blue` → `is-purple` → `is-orange` → `is-pink`). It matches the timeline gradient and reads as a progression from "early / foundation" to "mature / far".

For a 3-wave roadmap use `is-teal`, `is-purple`, `is-pink`. For a 4-wave roadmap use `is-teal`, `is-blue`, `is-orange`, `is-pink`.

## Template (HTML — fills `<div class="page" id="roadmap">`)

```html
<div class="page" id="roadmap">
  <h1>Your <span class="gradient">{{Roadmap heading}}</span></h1>
  <p class="lede">The ordered path from zero to <a href="#vision" onclick="document.querySelector('[data-page=vision]').click(); return false;">the Vision</a>.</p>

  <!-- Timeline bar (always right after the lede) -->
  <div class="timeline" style="--wave-count: 5">
    <span class="timeline-label is-teal">{{Wave 1 name}}</span>
    <span class="timeline-label is-blue">{{Wave 2 name}}</span>
    <span class="timeline-label is-purple">{{Wave 3 name}}</span>
    <span class="timeline-label is-orange">{{Wave 4 name}}</span>
    <span class="timeline-label is-pink">{{Wave 5 name}}</span>
    <div class="timeline-bar"></div>
  </div>
  <p class="timeline-hint">Tick boxes below to track your progress — {{total item count}} items across {{N}} waves.</p>

  <h2>How to read this</h2>
  <ul>
    <li>Waves are <strong>sequential</strong> — each depends on the prior wave's outcome.</li>
    <li>Tick items as you complete them. The checklist is visual only; progress isn't persisted — the shape of remaining work is the point.</li>
    <li>Each wave has <strong>success criteria</strong>. Don't skip them.</li>
  </ul>

  <h2>Where to start</h2>
  <p>New to this? Start at <strong>Wave 1: {{name}}</strong>. Already doing everything in Wave 1? Jump to Wave 2.</p>

  <!-- Wave 1 -->
  <section class="wave is-teal" data-wave="1">
    <span class="wave-tag">Wave 1 — {{phase label, e.g. Assistance}}</span>
    <h2>{{Wave 1 name}}: {{short subtitle}}</h2>
    <p>{{intro paragraph — what this wave does for the reader}}</p>

    <ul class="checklist two-col">
      <li><strong>{{Item name}}</strong> — {{concrete specifics}}</li>
      <li><strong>{{Item name}}</strong> — {{concrete specifics}}</li>
      <li><strong>{{Item name}}</strong> — {{concrete specifics}}</li>
      <li><strong>{{Item name}}</strong> — {{concrete specifics}}</li>
      <li><strong>{{Item name}}</strong> — {{concrete specifics}}</li>
    </ul>

    <p class="eyebrow">📚 Learning resources</p>
    <div class="resources">
      <a class="resource" href="{{url}}" target="_blank" rel="noopener">
        <span class="resource-source is-teal">GH Skill</span>{{resource title}}
      </a>
      <a class="resource" href="{{url}}" target="_blank" rel="noopener">
        <span class="resource-source is-blue">MS Learn</span>{{resource title}}
      </a>
    </div>

    <div class="outcome">
      <p class="eyebrow">Stage 1 outcome</p>
      <p>{{testable, observable end-state — 1–2 sentences}}</p>
    </div>
  </section>

  <!-- Wave 2 -->
  <section class="wave is-blue" data-wave="2">
    <span class="wave-tag">Wave 2 — {{phase label}}</span>
    <h2>{{Wave 2 name}}: {{subtitle}}</h2>
    <p>{{intro}}</p>
    <ul class="checklist two-col">
      <li><strong>{{Item}}</strong> — {{specifics}}</li>
      <!-- more items -->
    </ul>
    <p class="eyebrow">📚 Learning resources</p>
    <div class="resources">
      <a class="resource" href="{{url}}" target="_blank" rel="noopener">
        <span class="resource-source is-blue">MS Learn</span>{{title}}
      </a>
    </div>
    <div class="outcome">
      <p class="eyebrow">Stage 2 outcome</p>
      <p>{{end-state}}</p>
    </div>
  </section>

  <!-- Wave 3 (is-purple), Wave 4 (is-orange), Wave 5 (is-pink) — repeat pattern -->

  <h2>After the last wave</h2>
  <p>{{one short paragraph: what the reader is equipped to do, and a pointer to further reading / one-pagers / scale if present}}</p>
</div>
```

Notes:

- **Wave count is variable.** Adjust the `.timeline` `--wave-count` CSS variable to match (e.g. `style="--wave-count: 3"` for three waves). Labels and bar resize automatically.
- **`data-wave="N"` is load-bearing** — it's the number rendered in the circled marker (via `::before content: attr(data-wave)`). Don't omit it.
- **Resource source tags** — `.resource-source` text should name the *platform* (GH Skill, MS Learn, YouTube, Docs), not the topic. Tags are for scanning. Pick **one color per platform and keep it consistent across every wave** — e.g. GH Skill always `is-teal`, MS Learn always `is-blue`, Docs always `is-purple`. Scanning works because the color means the same thing everywhere; rotating within a wave defeats that.
- **Each wave is one slide in present mode.** The whole `<section class="wave">` — tag, heading, checklist, resources, outcome — renders on one slide. That's a lot on one slide; if a wave has >8 checklist items, split it into two waves (or move deep-dives to a companion page) rather than cramming.

## What NOT to do on the Roadmap section

- Don't hide sequencing behind "these can be done in parallel" unless you mean it. Most "parallel" phrasing masks a dependency.
- Don't mix inspiration with actions. The Roadmap is for actions; inspiration belongs in Vision.
- Don't cite resources you haven't used. Broken links or stale docs signal the whole site is stale.
- Don't add a wave because 3 waves felt short. Empty waves dilute the sequence. A 2-wave roadmap is fine if that's what the concept has.
- Don't use real `<input type="checkbox">` elements. The CSS `☐` prefix gives the visual without the fake-interactivity trap.
- Don't put a wave outside a `<section class="wave">` wrapper. Present-mode slide grouping depends on it.
