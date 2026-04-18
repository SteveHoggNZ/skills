# Intake

The purpose of intake is to surface enough material for the three load-bearing pages (Vision, Roadmap, Map) without fabricating anything. If any of the three can't be filled from the user's answers, stop and ask — don't proceed.

Write the user's answers back to them in a numbered list before scaffolding. Having them confirm (or edit) in one pass is cheaper than rewriting generated prose.

## Required fields

1. **Concept slug** — url-safe short name. E.g. `ai-sdlc`, `platform-2-0`, `zero-trust`.
2. **One-liner** — 12 words or fewer describing the concept. E.g. "The AI-native software development lifecycle."
3. **Audience** — who specifically needs to get aligned? Exec team? A specific department? All engineers? External stakeholders? (Different audiences pull the Vision in different directions.)
4. **Why now?** — what's changed that makes this worth a concept website this quarter? (Forcing function, new capability, incident, strategy pivot.)

## Vision material (top-down, the *why*)

5. **Destination state** — one paragraph describing the world in which this concept is fully realised. What does a day-in-the-life look like? What shifts?
6. **The core shift** — a "from X to Y" frame. E.g. "from humans writing every line to agents executing against intent definitions". The single sentence that captures the before/after.
7. **Pillars / principles** — 3 (preferred) or 4 durable principles the concept rests on. Each with a one-line definition. If the user has fewer than 3, ask them for a third — don't make one up.
8. **Moment-it-clicks example** — a concrete, short story or artefact that makes the concept feel real for a skeptic. What flipped for the user themselves when they got it?
9. **Journey / maturity levels** — how does an individual or team progress through this concept? Typically 3–5 levels (e.g. Maker → Engineering Manager → Architect of Intent).

## Roadmap material (bottom-up, the *how*)

10. **Waves** — 3–5 sequential adoption waves. Each wave is a phase, not a week. For each:
    - Short name (e.g. "Foundations", "Augmentation", "Orchestration", "Autonomy").
    - One-line outcome — what's true at the end of the wave that wasn't true at the start.
    - 3–8 concrete checkbox items — the actions / artefacts that constitute completion.
    - Success criteria — how you know the wave is actually done (not just claimed).
11. **Cross-wave resources** — links, docs, tools, templates the reader can pick up and use. Specific, not generic.

## Map material (bottom-up, the *layers*)

12. **Layers / stages** — the decomposition of the concept. For a lifecycle, this is the phases (Plan → Design → Code → Test → Review → Deploy → Operate → Maintain). For a capability, this is the tiers. For a platform, this is the subsystems. For each:
    - Layer name.
    - One-line purpose.
    - Readiness level — **Ready** / **Emerging** / **Preview** (or a comparable 3-tier scheme the user prefers).
    - One concrete current-state note per layer (what works today, what doesn't).

## Optional material (only when the user volunteers it)

13. **Foundations** — what does the reader need to know before the deep sections make sense? (Often a primer page.)
14. **Case study / steel thread** — a single end-to-end worked example that spans vision → map → roadmap.
15. **Scale** — how does this go from individual to team to org?
16. **One-pagers** — dense printable summaries for specific audiences (e.g. "for managers", "for SREs"). Each one-pager answers one question.

## Anti-patterns in intake answers

If any of these show up, push back before scaffolding:

- "It's a platform that enables teams to…" — too generic; press for the specific thing that's new.
- Pillars that restate each other (e.g. "fast", "efficient", "productive" — all the same principle).
- A roadmap wave with no success criteria ("roll it out widely").
- A map where every layer is "Emerging" — either the readiness tiers are wrong or the concept isn't ready for a site yet.
- No concrete moment-it-clicks example — means the concept is still abstract in the user's own head.

## Storing intake

Once the user confirms answers (or you've extracted them from attached source material in a non-interactive run), save them in the target directory as `data/intake.yml`. The site itself is plain HTML and does not read this file — it's a stable record of source material that later iterations (and `skill-iterate` probes) re-read rather than re-deriving from generated prose.

### Canonical schema

Use these top-level keys. They match the fields above; later iterations and the `skill-iterate` loop rely on this shape being stable across runs.

```yaml
concept_slug: ai-sdlc                    # field 1
one_liner: "…"                           # field 2
audience: "…"                            # field 3
why_now: "…"                             # field 4

destination_state: "…"                   # field 5 (one paragraph)
core_shift:                              # field 6
  from: "…"
  to: "…"
pillars:                                 # field 7 (3 preferred, 4 max)
  - name: "…"
    definition: "…"                      # one sentence
    expansion: "…"                       # one paragraph
    rules_out: "…"                       # optional
moment_it_clicks: "…"                    # field 8
journey:                                 # field 9 (3–5 levels)
  - level: 1
    name: "…"
    signal: "…"                          # "you know you're here when…"

waves:                                   # field 10 (3–5)
  - name: "…"
    outcome: "…"                         # one line
    why_now: "…"                         # optional, 1–2 sentences
    checklist:                           # 3–8 concrete items
      - "…"
    resources:                           # specific links, not reading lists
      - title: "…"
        url: "…"
        why: "…"
    success_criteria:                    # testable conditions
      - "…"

map_layers:                              # field 12
  - name: "…"
    purpose: "…"                         # one line
    readiness: ready                     # ready | emerging | preview
    ready_today:                         # bullets with links
      - "…"
    on_horizon:                          # optional; use [] if "None yet"
      - "…"
    engage: "…"                          # Roadmap wave / resource / deep-dive link

metaphors:                               # 1–3, reused across the site
  - "execution is cheap, clarity is expensive"
```

Optional material (only if the user volunteered it; omit keys entirely rather than including empty placeholders):

```yaml
foundations: "…"                         # field 13
case_study:                              # field 14
  name: "…"
  summary: "…"
scale: "…"                               # field 15
one_pagers:                              # field 16
  - title: "…"
    audience: "…"
    question_answered: "…"
```
