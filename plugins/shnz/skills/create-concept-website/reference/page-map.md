# Section: Map (the *layers* / *stages*)

The Map section decomposes the concept into its parts and shows readiness for each. It's what the reader reaches for when they want to know "what exactly are the pieces of this thing?". It bridges the Vision's abstraction and the Roadmap's sequencing: the Vision says where; the Roadmap says how; the Map says **what**.

For lifecycle concepts, the map is the lifecycle stages (Plan → Design → Code → Test → Review → Deploy → Operate → Maintain). For capability / platform concepts, it's the tiers or subsystems. For org-change concepts, it's the function-level decomposition.

## Structure (in order)

1. **Intro** — `<h1>` + `.lede`.
2. **Legend** — a small table mapping the three badges (Ready / Emerging / Preview) to meanings. Eyebrow `THE LEGEND` above it.
3. **At a glance** — pick one shape:
   - **Hex grid** (preferred for lifecycle-shaped concepts): `.hex-grid` with one `.hex` per phase. Feels modern, inherits site typography, reads as a loop. Best when the Map *is* the lifecycle (e.g. 6–8 phases that loop back). See [diagrams.md](./diagrams.md) §`.hex-grid`.
   - **Card grid**: `.cards` with one `<a class="card">` per layer — name, readiness badge, one-line purpose. Each card links to the layer's anchor below. Best when layers are not sequential and the reader scans for readiness.
   - **Mermaid flowchart** (fallback): one `<pre class="mermaid">` inside a `<figure class="diagram">` rendering a `flowchart LR`. Use when the layer relationships have branches or joins that a hex grid cannot convey. No node-fill colours; readiness via `classDef` stroke only. See [diagrams.md](./diagrams.md) §Mermaid.
   Pick one, not all three. A good Map has exactly one diagram at the top and one summary table at the bottom.
4. **One layer per `<h2>` section**, with `id="layer-N"` for the at-a-glance cards to target. Each has:
   - Readiness badge inline in the heading (`<span class="badge badge-ready">Ready</span>`).
   - `<strong>Purpose:</strong>` one line.
   - `<p class="eyebrow">What's ready today</p>` + bullet list.
   - `<p class="eyebrow">What's on the horizon</p>` + bullet list, or `<p>None yet.</p>`.
   - `<strong>How to engage:</strong>` one-line pointer to a Roadmap wave or resource.
5. **Summary table** — scannable Layer | Purpose | Readiness | Next table at the bottom. The printable "cheat sheet" version of the map.

## Voice

- **Specific, not evaluative.** "Supports pinned reproducible builds across 14 repos" beats "This layer is mature".
- **Readiness claims are testable.** Ready = "list the tools / links that prove it". Emerging = "first teams are using it". Preview = "prototype; not a commitment yet".
- **Symmetric structure.** Every layer has the same subsections in the same order. If one has no "on horizon" entries, write "None yet." explicitly rather than omitting the heading.

## Template (HTML — fills `<div class="page" id="map">`)

```html
<div class="page" id="map">
  <h1>The Map</h1>
  <p class="lede">How {{concept}} decomposes into layers, and what's ready today.</p>

  <p class="eyebrow">The legend</p>
  <h2>Readiness levels</h2>
  <table>
    <thead><tr><th>Badge</th><th>Meaning</th></tr></thead>
    <tbody>
      <tr><td><span class="badge badge-ready">Ready</span></td><td>In use; supported; documented. Safe to adopt.</td></tr>
      <tr><td><span class="badge badge-emerging">Emerging</span></td><td>First teams using it. Expect rough edges. Feedback wanted.</td></tr>
      <tr><td><span class="badge badge-preview">Preview</span></td><td>Prototype or early proposal. Not a commitment yet.</td></tr>
    </tbody>
  </table>

  <p class="eyebrow">At a glance</p>
  <h2>{{Overview heading — e.g. "Every layer, every badge"}}</h2>

  <!-- Option A (preferred for lifecycle-shaped concepts): HTML-native hex grid.
       Inherits site typography, prints well, no runtime dep. -->
  <figure class="diagram">
    <div class="hex-grid">
      <div class="hex"><div class="hex-inner"><h4>{{Layer 1}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 2}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 3}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 4}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 5}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 6}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 7}}</h4><p>{{2-word purpose}}</p></div></div>
      <div class="hex"><div class="hex-inner"><h4>{{Layer 8}}</h4><p>{{2-word purpose}}</p></div></div>
    </div>
    <figcaption>{{One sentence; mention if the last phase loops back to the first.}}</figcaption>
  </figure>

  <!-- Option B (non-sequential layers / readiness-first scan): card grid. -->
  <!--
  <div class="cards">
    <a class="card" href="#layer-1" onclick="document.getElementById('layer-1').scrollIntoView({behavior:'smooth'}); return false;">
      <h3>{{Layer 1 name}} <span class="badge badge-ready">Ready</span></h3>
      <p>{{one-line purpose}}</p>
    </a>
    …
  </div>
  -->

  <!-- Option C (fallback, branching/joining layers): mermaid flowchart.
       See reference/diagrams.md §Mermaid. -->


  <h2 id="layer-1">{{Layer 1 name}} <span class="badge badge-ready">Ready</span></h2>
  <p><strong>Purpose:</strong> {{one line}}</p>

  <p class="eyebrow">What's ready today</p>
  <ul>
    <li>{{capability / tool / artefact}} — <a href="{{url}}" target="_blank" rel="noopener">{{link label}}</a></li>
    <li>{{capability}} — <a href="{{url}}" target="_blank" rel="noopener">{{link}}</a></li>
  </ul>

  <p class="eyebrow">What's on the horizon</p>
  <ul>
    <li>{{near-term addition, only if concrete from intake}}</li>
  </ul>
  <!-- If none, replace the <ul> with: <p>None yet.</p> -->

  <p><strong>How to engage:</strong> <a href="#roadmap" onclick="document.querySelector('[data-page=roadmap]').click(); return false;">Wave N of the Roadmap</a> / {{resource}}</p>

  <h2 id="layer-2">{{Layer 2 name}} <span class="badge badge-emerging">Emerging</span></h2>
  <!-- repeat the same sub-structure -->

  <p class="eyebrow">The big picture</p>
  <h2>Summary</h2>
  <table>
    <thead>
      <tr><th>Layer</th><th>Purpose</th><th>Readiness</th><th>Next</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="#layer-1">{{layer 1}}</a></td>
        <td>{{purpose}}</td>
        <td><span class="badge badge-ready">Ready</span></td>
        <td>{{next}}</td>
      </tr>
      <tr>
        <td><a href="#layer-2">{{layer 2}}</a></td>
        <td>{{purpose}}</td>
        <td><span class="badge badge-emerging">Emerging</span></td>
        <td>{{next}}</td>
      </tr>
    </tbody>
  </table>
</div>
```

Notes:

- The `id="layer-N"` on `<h2>` lets the at-a-glance cards deep-link directly to each layer. Keep ids stable if you reorder.
- The `.cards` grid is from the base scaffold; no layer-specific variant is required here. Use a plain `<a class="card">` per layer.
- For a site with > 8 layers, consider moving the Map content into a dedicated companion page (like the reference's `sdlc-map.html`). Link it from the main nav. The component classes and templates work identically in a standalone HTML file.

## What NOT to do on the Map section

- **Don't pile every diagram type into the Map.** One shape at "At a glance" (flowchart or card grid, not both) plus one summary table at the bottom. Mermaid is supported by the scaffold (lazy-loaded CDN — see [diagrams.md](./diagrams.md)), but a second diagram in the same section is almost always noise.
- Don't invent "Emerging" entries to pad a layer. If a layer has nothing on the horizon, write "None yet." That honesty is what keeps the map trustworthy.
- Don't mark everything Ready or everything Emerging. A uniform map is a signal the readiness tiers aren't well-defined.
- Don't cross-link so aggressively that the Map becomes a link-dump. Each layer should link out to at most 2 resources.
- Don't describe the layers as a sequence. That's the Roadmap's job. The Map is a *topology*; the Roadmap is an *order*.
