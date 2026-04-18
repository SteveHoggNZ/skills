# Section: Vision (the *why*)

The Vision section is the top-down half of the site. It's narrative, aspirational, and makes the concept feel real. It exists so the reader — after one read — can state the one-line shift, name the pillars, and picture the destination state.

It's also the **hardest section to write well**. Draft it last (after Map and Roadmap), so you know what "the how" actually looks like and can avoid the failure mode: disconnected aspiration.

## Structure (in order)

Follow this structure unless the user's material strongly pushes against it. It's tuned to the reference site's arc: destination → frame → picture → pillars → moment-it-clicks → journey.

Every `<h2>` is preceded by a `<p class="eyebrow">` — a short uppercase colored label that names the section's role ("THE DESTINATION", "THREE PILLARS", "YOUR JOURNEY"). Eyebrows orient the reader before the heading lands.

1. **Destination** — one paragraph + before/after contrast. Destination-state from intake verbatim where possible. Pair with a concrete before-image so the delta is visible.
2. **Big picture** — the "from X to Y" single-sentence shift in a `<blockquote>`. Give it its own quote; it's the sentence the reader will repeat to someone else.
3. **<Concept> in motion** — a **flow narrative** showing how the parts connect when the concept is alive. Use the `.flow` component: colored badge → arrow → description, one row per step. This is the component that makes the section feel *alive* (not just a table of steps).
4. **Pillars** — 3 (preferred) or 4 named principles, each a `.pillar` card with icon tile + colored top-border + body. Variants: `is-orange`, `is-teal`, `is-pink`, `is-blue`, `is-purple`.
5. **The moment it clicks** — a single concrete story in a `<blockquote>` with **inline accent highlights** (`<span class="hl-pink">`, `<span class="hl-orange">`, `<span class="hl-teal">`) on the load-bearing terms. The highlights are what makes the paragraph scannable at slide distance.
6. **Your journey** — 3–5 `.journey-card`s in a row. Each has a `<p class="eyebrow">WHERE YOU START</p>`, a colored `<p class="role">Maker</p>`, and a short body. Variants match the "ascent" (is-orange → is-blue → is-purple works well).

## Voice

- **Narrative, not listy.** The Vision section is the one place to write paragraphs rather than bullets. Bullets everywhere reads as a slide deck and loses the narrative pull.
- **Reuse the chosen metaphors** from intake. A metaphor that lands is worth 10 abstract sentences.
- **Concrete over abstract.** If a sentence could describe five other concepts, cut it or specialise it.
- **Confidence, not hedging.** "When the concept is fully realised" beats "when the concept is largely realised across most organisations".
- **Second person is fine** when talking about the reader's journey. Avoid first-person plural ("we believe…").

## Template (HTML — fills `<div class="page" id="vision">`)

```html
<div class="page active" id="vision">
  <h1>Where We're <span class="gradient">Heading</span></h1>
  <p class="lede">{{one-liner from intake}}</p>

  <p class="eyebrow">The destination</p>
  <h2>{{Destination heading — e.g. "What You're Building Towards"}}</h2>
  <p>{{destination paragraph from intake}}</p>
  <p><strong>Today:</strong> {{concrete current-state image}}<br>
     <strong>Tomorrow:</strong> {{concrete destination image}}</p>

  <p class="eyebrow">The big picture</p>
  <h2>{{Shift heading — e.g. "From Writing Code to Defining 'Correct'"}}</h2>
  <blockquote>From <strong>{{X}}</strong> to <strong>{{Y}}</strong>.</blockquote>
  <p>{{one paragraph expanding the shift — what it implies, what it does not imply}}</p>

  <p class="eyebrow">The {{concept}} in motion</p>
  <h2>{{Motion heading — e.g. "A Ticket, End-to-End"}}</h2>
  <p>{{one-sentence setup}}</p>
  <div class="flow">
    <div class="flow-row is-teal">
      <div class="flow-badge">📄 {{Step 1 label}}</div>
      <div class="flow-arrow">→</div>
      <div class="flow-body"><strong>{{Actor}}</strong> {{action description}}</div>
    </div>
    <div class="flow-row is-blue">
      <div class="flow-badge">🔍 {{Step 2 label}}</div>
      <div class="flow-arrow">→</div>
      <div class="flow-body"><strong>{{Actor}}</strong> {{action description}}</div>
    </div>
    <div class="flow-row is-purple">
      <div class="flow-badge">☑ {{Step 3 label}}</div>
      <div class="flow-arrow">→</div>
      <div class="flow-body"><strong>You</strong> {{description}}</div>
    </div>
    <div class="flow-row is-orange">
      <div class="flow-badge">⚡ {{Step 4 label}}</div>
      <div class="flow-arrow">→</div>
      <div class="flow-body"><strong>{{Actor}}</strong> {{action description}}</div>
    </div>
    <div class="flow-row is-pink">
      <div class="flow-badge">🚀 {{Step 5 label}}</div>
      <div class="flow-arrow">→</div>
      <div class="flow-body"><strong>{{Actor}}</strong> {{action description}}</div>
    </div>
  </div>
  <p>{{one-sentence observation: where the human enters, what the harness does}}</p>

  <p class="eyebrow">Three pillars</p>
  <h2>{{Pillars heading — e.g. "What Makes This Work"}}</h2>
  <p>{{one-line intro — what the pillars rest on, link to Roadmap}}</p>
  <div class="pillar-grid">
    <article class="pillar is-orange">
      <div class="pillar-icon">🎯</div>
      <h3>{{Pillar 1 name}}</h3>
      <p>{{one-sentence definition + one concrete example}}</p>
    </article>
    <article class="pillar is-teal">
      <div class="pillar-icon">🛡️</div>
      <h3>{{Pillar 2 name}}</h3>
      <p>{{one-sentence definition + one concrete example}}</p>
    </article>
    <article class="pillar is-blue">
      <div class="pillar-icon">📄</div>
      <h3>{{Pillar 3 name}}</h3>
      <p>{{one-sentence definition + one concrete example}}</p>
    </article>
  </div>

  <p class="eyebrow">The moment it clicks</p>
  <h2>{{Moment heading — e.g. "When the Harness Becomes the Teacher"}}</h2>
  <p>There's a specific moment in the journey when everything comes together. It looks like this.</p>
  <blockquote>
    {{first beat of the story}} The <span class="hl-pink">{{dramatic term 1}}</span>.
    {{next beat}} A <span class="hl-orange">{{dramatic term 2}}</span>.
    {{final beat}} <span class="hl-teal">{{dramatic term 3}}</span>. {{closing line.}}
  </blockquote>
  <p>{{one-sentence takeaway — what the story teaches}}</p>

  <p class="eyebrow">Your journey</p>
  <h2>{{Journey heading — e.g. "How Your Role Changes"}}</h2>
  <p>{{one-line intro — reader-facing, confident}}</p>
  <div class="journey">
    <div class="journey-card is-orange">
      <p class="eyebrow">Where you start</p>
      <p class="role">{{Level 1 name}}</p>
      <p>{{one-paragraph signal — "you know you're here when…"}}</p>
    </div>
    <div class="journey-card is-blue">
      <p class="eyebrow">Where you grow</p>
      <p class="role">{{Level 2 name}}</p>
      <p>{{signal}}</p>
    </div>
    <div class="journey-card is-purple">
      <p class="eyebrow">Where you're heading</p>
      <p class="role">{{Level 3 name}}</p>
      <p>{{signal}}</p>
    </div>
  </div>

  <p class="eyebrow">The path</p>
  <h2>{{Path heading — e.g. "How We Get There"}}</h2>
  <p>{{one-sentence — how the Roadmap + Map let the reader act on the Vision}}</p>
  <div class="path">
    <a class="path-tile" href="#roadmap" onclick="document.querySelector('[data-page=roadmap]').click(); return false;">
      <span class="path-emoji">🗺️</span>
      <span class="path-label is-teal">Roadmap</span>
      <span class="path-note">Your checklist</span>
    </a>
    <a class="path-tile" href="#map" onclick="document.querySelector('[data-page=map]').click(); return false;">
      <span class="path-emoji">🧭</span>
      <span class="path-label is-blue">Map</span>
      <span class="path-note">The layers</span>
    </a>
  </div>
</div>
```

Notes:

- Emojis in `.flow-badge` and `.pillar-icon` are placeholders; pick one per item that's *category-appropriate* (📄 ticket, 🔍 research, ☑ review, ⚡ implement, 🚀 deploy; 🎯 intent, 🛡️ physics, 📄 artefact). Don't pile emojis into prose — only use them as iconography in these components.
- The `.path` row at the end acts as an inline nav pointer back to the tactical sections. It's an accessibility-friendly alternative to "next: click the Roadmap tab" — the tiles *are* the next step.
- On very short Vision sections, skip the motion/path sections — the structure is a ceiling, not a floor.

## What NOT to do on the Vision section

- Don't replace `.flow` with a plain table. The flow gives the narrative spatial pacing (badge + arrow + body) that a table doesn't.
- Don't list every feature / capability. That's for the Map.
- Don't use the `.wave` marker here. That's reserved for the Roadmap — reusing it dilutes the visual language.
- Don't include wave checkboxes. That's for the Roadmap.
- Don't write more than ~900 words of body text. A Vision that can't be read in 3 minutes won't be re-read, and Vision sections are re-read.
- Don't inline-highlight more than ~3 terms per blockquote. Highlights work because they're rare; pepper them and the reader stops noticing.
