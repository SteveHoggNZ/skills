# HMR can't replace context providers

A specific Vite gotcha that wastes hours when you don't know it.

## The bug shape

You edit a React context provider — change a hook, add a state field, modify the value shape. Save. Vite's HMR shows `[vite] (client) hmr update /src/contexts/MyContext.tsx` in the dev server log. The browser appears to reload.

But the new code isn't running. Components consuming the context still see the old behaviour. You add `console.log` to verify — your log doesn't appear. You rebuild. Nothing changes. You start questioning your sanity.

## Why this happens

React context providers participate in the React tree. When HMR replaces the module that defines the provider, the existing provider instance in the tree stays alive — the *new* module is loaded, but the React tree never re-mounts it. The consumers continue to subscribe to the old provider's value.

Vite logs an `hmr invalidate` message when this happens for a Fast Refresh-incompatible module:

```
[vite] (client) hmr invalidate /src/contexts/MyContext.tsx Could not Fast Refresh
("ContextValue" export is incompatible).
```

But this only triggers a *deferred* reload — on the next navigation or HMR of an importing module. A plain `Cmd-R` from the user is not enough; the cached module graph still has the stale version.

## The diagnostic

Quickest way to confirm this is your bug:

```bash
# 1. Confirm the source file on disk has the new code
grep 'expected-new-string' src/contexts/MyContext.tsx

# 2. Confirm the dev server is serving the new code
curl -s -H 'Sec-Fetch-Dest: script' -H 'Referer: http://localhost:port/' \
  'http://localhost:port/src/contexts/MyContext.tsx' | grep 'expected-new-string'

# 3. If both show the new code but the browser doesn't, you have HMR-context-stall
```

If step 1 fails: you didn't actually save / didn't edit the right file.
If step 2 fails but step 1 passes: the dev server has a stale transform cache. Restart it (see below).
If both pass but the browser is stale: the browser has a stale module graph. Cache-bust the URL.

## The fix

### For the user / browser

Cache-bust the URL with any query parameter:

```
http://localhost:4173/?…&_b=1234567
```

Plain `location.reload()` is not enough. `Cmd-Shift-R` may or may not be enough depending on the browser. The `?_b=` query param forces Vite to treat it as a fresh navigation, which re-initialises the React tree.

For stubborn cases (service workers, etc.), open in an Incognito window — fresh context, no caches.

### For the dev server

Sometimes Vite's *own* transform cache is stale (seen with `tanstack-start` plugin). The browser is receiving an old version because Vite hasn't recompiled the source.

Symptoms: `curl` of the source file (with the right `Sec-Fetch-Dest: script` header) returns old content despite the file on disk being new.

Fix:

```bash
# Stop the dev server, kill the port (just `restart` doesn't always free it),
# then start fresh. Adjust paths/ports for your project.
docker compose exec -T amp-dev bash -c "
  supervisorctl stop dev-ui &&
  lsof -ti:4173 | xargs -r kill -9 &&
  sleep 2 &&
  supervisorctl start dev-ui
"
```

For severe cases (adding a new `createServerFn`, adding a new export to a heavily-imported module), nuke Vite's on-disk caches:

```bash
rm -rf node_modules/.vite .tanstack/  # or your framework's equivalent
```

## How to avoid it preemptively

When editing a file that's heavily consumed across the React tree (especially context providers, root layouts, query clients), assume HMR will not be enough. Either:

- **Cache-bust your URL** as a habit when developing context-provider changes.
- **Restart the dev server** explicitly after the change.
- **Open Incognito** as your second-window for "did this actually deploy" checks.

It's annoying but cheaper than spending 20 minutes debugging "my fix isn't working" only to discover the fix was right and the browser was lying.

## Recognising it in the wild

Smells:

- "I changed X, hard-reloaded, the change isn't applying."
- "Works in Incognito, broken in my main browser."
- "My console.log isn't firing even though the line is definitely there."
- Vite log shows `hmr invalidate ... Could not Fast Refresh ("X" export is incompatible)`.

When you see any of these, suspect this gotcha first before assuming your code is wrong.

## Pairs with

- [dont-trust-screenshots.md](./dont-trust-screenshots.md) — the broader principle. The user's "still broken" report is often this gotcha.
- [instrumentation-patterns.md](./instrumentation-patterns.md) — when your debug instrumentation isn't firing, suspect HMR-context-stall.
