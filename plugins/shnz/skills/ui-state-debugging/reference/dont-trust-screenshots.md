# Don't trust screenshots

The user's screenshot is **one observer's view at one moment in one bundle**. It is not ground truth. Always reproduce yourself before declaring a bug fixed *or* before accepting that a fix didn't work.

## Why screenshots lie

A screenshot can show a bug that no longer exists, or fail to show a bug that's actively occurring, for any of the following reasons:

- **Stale JS bundle.** The user's tab has been open for hours. HMR reloaded *some* modules but couldn't replace others (especially React context providers — see [hmr-context-providers.md](./hmr-context-providers.md)). The user is running a mix of old and new code.
- **Cached API response.** React Query / Apollo cached an early response and hasn't refetched. The DOM reflects the cached data, which is no longer what the API would return.
- **Service worker cache.** A PWA's service worker is serving an old bundle from disk. `Cmd-R` doesn't clear it. `Cmd-Shift-R` may not either.
- **CDN cache.** Less common in dev, but in staging/prod, CloudFront or similar may be serving an older response than what the API now returns.
- **Different account / session.** The user is logged in as someone whose data really is in that state. The bug only manifests for that account.
- **Race condition in initial load.** The first render captured a moment that recovers seconds later. The screenshot is correct *for that moment* but the bug is intermittent.
- **Browser zoom / responsive layout.** The "missing element" is just below the fold or hidden by responsive CSS at the user's viewport.

## The verification protocol

Before responding to "still broken" / "now fixed":

### 1. Reproduce in your own session

Open the same URL in your own browser (or a fresh agent-browser session, or a Playwright launch). Use a cache-busted URL (`?_b=${Date.now()}`).

If you see the bug → it's real, investigate.
If you don't see the bug → the user's session is stale. Confirm what code they're running:

```bash
# Verify what JS the dev server is actually serving
curl -s -H 'Sec-Fetch-Dest: script' -H 'Referer: http://localhost:port/' \
  'http://localhost:port/src/path/to/file.tsx' | grep 'expected-new-string'
```

If the served file has the fix but the user's tab doesn't, instruct them to hard-reload with cache-bust. If the served file *doesn't* have the fix, the dev server is also stale — restart it (kill the port, not just `restart`).

### 2. Check the data layer

Query the database for the entity in the screenshot. Does the screenshot match what's persisted?

If yes — the bug isn't a UI bug, it's an upstream/data bug. The user's screenshot is correct evidence of a real wrong-state.
If no — the user's UI is stale. Their screenshot is correct evidence of a stale UI, not the bug they think they're reporting.

### 3. Compare what the API returns now to what the user sees

```bash
curl -s -H 'Authorization: …' 'http://host/api/…' | jq .
```

Compare to the screenshot. If they disagree, the user's client is stale. Reproduce step 1 in a fresh session.

### 4. Drive the test yourself

Don't ask the user to retest. **You** retest. With a fresh browser context, with cache-bust, with their exact channel/entity ID.

## The protocol in compact form

```
User: "still broken" / "now fixed"
↓
You: 1. Open the same URL in YOUR session, cache-busted
     2. Compare to what the DB says
     3. Compare to what the API says fresh
     4. Find the first divergence
     5. THAT is the actual bug or non-bug
```

Never declare a fix verified based solely on the user's word or a single screenshot from them.

## Why this matters

Multiple iterations of "fix → user reports broken → debug → fix the wrong thing" can be entirely caused by stale-bundle false reports. Catching the staleness one iteration in saves multiple wasted hours of fixing problems that don't exist.

## When the user says "I hard-reloaded"

A hard reload (`Cmd-Shift-R` in Chrome) busts the HTTP cache for the document and immediate dependencies. It does **not** always cleanly destroy:

- React's in-memory module graph if HMR has already poisoned it.
- IndexedDB / localStorage state.
- Service worker caches without explicit unregister.

For stubborn cases, instruct the user to:

1. Open DevTools.
2. Network panel → check "Disable cache".
3. Application panel → Storage → "Clear site data".
4. Reload.

OR — and this is faster — just open the URL in an Incognito window. Fresh context, no caches, no extensions.

## A note on inversion

The protocol also catches the *opposite* case: the user reports "fixed" when the bug actually still exists, but their cached version happens to render correctly for the entity they're looking at while the underlying bug persists for other entities. Reproducing in a fresh session catches this too.
