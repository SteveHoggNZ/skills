# Test rig pattern

The shape of a good repro harness for UI state bugs. **Patterns, not a template** — write a fresh rig each time, drawing on these patterns. Templates rot; understanding doesn't.

## What a test rig is

A test rig is a Playwright (or Puppeteer) script that:

1. **Reproduces a bug deterministically** by setting up the exact preconditions.
2. **Records the session** (video + DOM snapshots at intervals + console logs).
3. **Dumps a structured timeline** that can be diffed across runs to verify a fix.

It's not a unit test. It's not an end-to-end test. It's a **diagnostic instrument** — write it when you're debugging something hard, throw it away or upgrade it to a real test once the bug is fixed.

## When to build one

Build a rig when:

- The bug only reproduces under specific timing or state setup that's tedious to recreate by hand.
- You need to **verify a fix** without depending on the user retesting.
- You want a **before/after artifact** (video + report) you can show in the PR.
- Multiple iterations are likely — build the rig once, run it many times.

Don't build a rig when:

- The bug reproduces in 3 clicks. Just inspect by hand.
- You can fix it in 5 minutes from inspection alone.

## The shape

A good rig has six parts. Skipping any of them costs more time than including it.

### 1. Set up preconditions deterministically

```ts
async function setupChannel(page: Page): Promise<string> {
  await page.locator('button[aria-label="New channel"]').click()
  await page.waitForTimeout(1500)
  const url = page.url()
  const channelId = url.match(/channel=([0-9a-f-]{36})/)?.[1]
  if (!channelId) throw new Error('no channel id in URL')

  // add the agent we need to trigger the bug
  await page.locator('button[aria-label="Manage members"]').click()
  // ... etc
  return channelId
}
```

The point: **the rig owns its preconditions**. Don't assume a channel exists, don't reuse stale state from prior runs.

### 2. Trigger the bug condition

```ts
await page.locator('.composer').type('@MyAgent start')
await page.locator('button:has-text("Send")').click()
```

This is the part that varies most across rigs — it's the user action that triggers the bug.

### 3. Sample the state at intervals

```ts
const intervals = Math.floor(RECORD_SECONDS / 5)
const timeline: Array<{ t: number; bubbles: BubbleSnapshot[] }> = []

for (let i = 0; i < intervals; i++) {
  await page.waitForTimeout(5000)
  const snap = await snapshotBubbles(page)
  console.log(`[t=${(i+1)*5}s]`, snap.map(b => `${b.id}: ${b.status}`).join(' | '))
  timeline.push({ t: (i+1)*5, bubbles: snap })
}
```

Why a structured array: human-readable progress in the console *and* a machine-diffable artifact for assertion.

### 4. Dump diagnostics from the live page

```ts
const diag = await page.evaluate(() => {
  const w = window as any
  return {
    streamStatusEvents: (w.__sseEvents ?? []).map(e => ({ ts: e.ts, kind: e.kind, id: e.id })),
    cacheState: (w.__cacheDebug ?? []).slice(-50),
  }
})
require('node:fs').writeFileSync(`${outDir}/diagnostics.json`, JSON.stringify(diag, null, 2))
```

This is where the rig pairs with [instrumentation-patterns.md](./instrumentation-patterns.md) — the rig page-loads with debug instrumentation in the source code, then dumps the captured state at the end of the session.

### 5. Record video

```ts
const context = await browser.newContext({
  viewport: { width: 1400, height: 900 },
  recordVideo: { dir: outDir, size: { width: 1400, height: 900 } },
})
// ... run the test
await context.close() // closes the video file
```

Video is for human review (PR attachments, Loom replacements). The structured timeline is for assertion.

### 6. Write a report

```ts
const report = [
  `# ${BUG_NAME} — repro`,
  `Generated ${new Date().toISOString()}`,
  ``,
  `## Bubble timeline (5s intervals)`,
  ...timeline.map(t => `### t=${t.t}s\n${t.bubbles.map(b => `- ${b.id}: ${b.status}`).join('\n')}`),
  ``,
  `## Verdict`,
  `Bug ${verdict ? 'FIXED' : 'PRESENT'}: ${reason}`,
].join('\n')
fs.writeFileSync(`${outDir}/report.md`, report)
```

The report is the single artifact you point at when discussing the rig's findings. Video, JSON diagnostics, and report all in one timestamped output dir.

## Anti-patterns

### Sharing state across rigs

Each rig run should be **hermetic** — fresh channel, fresh setup, fresh timestamps. Reusing channel state across runs makes the rig non-deterministic.

If setup is expensive and you need to share, snapshot the state file at the start and restore it. Don't depend on the previous run's leftovers.

### Using `waitForLoadState('networkidle')`

Apps with SSE / WebSocket connections never reach `networkidle` — the connection stays open. Use `domcontentloaded` and explicit waits for specific selectors instead.

### Hardcoding channel IDs

The rig should create its own channel each run. Hardcoded IDs (especially "the channel I was debugging in") leave you debugging stale data from yesterday.

### Skipping the diagnostics dump

Without `__myDebug` push + dump, the video is the only artifact. Videos are great for spotting the symptom, terrible for diffing what changed in the data flow. Always dump structured state.

### "Run this rig and tell me if it's fixed"

The rig's verdict should be **deterministic**. Compute the verdict in the script (`bubbles.every(b => b.status === 'expected')`), don't ask the human reviewing the artifact to eyeball it. If you can't write the verdict assertion, you don't yet understand the bug.

## Where rigs live

In the **target repo**, not in the skill. Rigs are codebase-coupled — they reference DOM selectors, route paths, agent names that mean nothing outside the project.

Conventional location: `<repo>/scripts/test-rigs/<bug-name>/`. Output goes to `<repo>/.ai/plans/<plan>/runs/` or similar — gitignored if it gets large.

The **patterns** live here in this skill. The **rigs themselves** live in the repo. See [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md) for the resource matrix.

## Lifecycle of a rig

1. **Scratch** — written for one bug, lives in `scripts/test-rigs/<name>/`.
2. **Promoted** — if the rig keeps catching regressions, port it to a real integration test in the repo's test suite. The integration test loses the video recording (CI doesn't need it) but gains durability.
3. **Deleted** — if the rig is no longer relevant, delete it. Don't let dead rigs accumulate; they make `find scripts/test-rigs` noisy.

## Worked example shape

A good rig is ~100-200 lines of TypeScript, mostly app-specific. The Playwright glue (browser launch, video recording, snapshot intervals) is ~30 lines you'll write fresh each time. The remaining ~70-170 is the codebase-specific setup, trigger, and assertion.

If you find yourself extracting "the generic 30 lines" into a template, you're building a framework. Don't. Each rig is small enough that fresh-write beats template-customise.
