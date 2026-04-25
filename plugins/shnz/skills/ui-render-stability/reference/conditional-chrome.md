# Conditional layout chrome

The most common cause of visible flashes during state transitions. Tabs, headers, side panels, and other layout chrome are rendered conditionally on data state, so they mount and unmount as data loads — producing visible layout shifts.

## What it looks like

In your before/after frames around a transition:

- A tab strip is present in one frame and absent in the next (or vice versa).
- A right-side panel pops in/out of existence.
- A header button appears or disappears.
- A toolbar's button count changes.

The flash is the layout reflowing to fill (or yield) the space the chrome was occupying. Even if the visible content underneath is correct, the user perceives the screen as "jumping."

## The anti-pattern in code

```tsx
// ❌ Conditional rendering of layout chrome
function ChannelView({ channel }) {
  return (
    <div>
      <ChannelHeader channel={channel} />
      {channel.frames.length > 0 && <TabStrip frames={channel.frames} />}
      {channel.workflowFrame && <WorkflowTab />}
      {channel.hasMessages && <MessagesTab />}
      <MainPane channel={channel} />
    </div>
  )
}
```

Every conditional `&&` is a place the layout will mount/unmount as `channel.X` changes from undefined → empty array → populated. Each transition is a flash.

## The fix: persistent layout, conditional content

```tsx
// ✅ Layout always present; content varies
function ChannelView({ channel }) {
  return (
    <div>
      <ChannelHeader channel={channel} />
      <TabStrip frames={channel.frames ?? []} />     {/* renders even when empty */}
      <WorkflowTab disabled={!channel.workflowFrame} />
      <MessagesTab placeholder={!channel.hasMessages} />
      <MainPane channel={channel} />
    </div>
  )
}
```

The chrome is always rendered. Empty / disabled / placeholder states fill the space and tell the user "this exists but isn't ready" — without removing the layout slot.

## When conditional chrome is correct

Not every conditional render is wrong. Two cases where it's the right call:

1. **Truly different routes** — going from `/login` to `/app` legitimately swaps the entire layout. There's no chrome continuity to preserve.
2. **Permission-gated chrome** — an admin-only menu shouldn't render for non-admins (and the flash on permission change is unavoidable + rare). The layout should still be stable for users in one role; just not across role transitions.

The wrong cases are within a single user session, single permission level, single route — where chrome should be a stable scaffold.

## Diagnosing in code

Once your video frames identify "tab strip mounted/unmounted at t=3.01", grep the codebase for the chrome's component name:

```bash
grep -rn "TabStrip\|<TabStrip" src/ | grep -v test
```

Look at every render site. Each `{cond && <TabStrip>}` is a candidate. Often you can trace which `cond` flipped between true and false by looking at what the user did just before the flash.

## The "tabs depend on frames" trap

A common case: tabs are conditionally rendered based on whether the corresponding frames exist (`{hasWorkflowFrame && <WorkflowTab>}`). The user's perception is "I created a new channel and the tabs flickered" — they don't know the tabs are tied to frames.

Fix: render the tab unconditionally with a "no workflow yet" empty state. The slot is stable; the content within reflects the data.

## When the chrome data is async

If the chrome's *content* depends on data that loads (e.g. tab labels come from a remote schema fetch), don't conditionally render the tabs while loading. Instead:

- Render tab placeholders with the right shape (skeleton bars).
- Swap to real labels on load.

Skeleton tabs in the right places don't shift layout; conditional tabs do.

## Pairs with

- [skeleton-states.md](./skeleton-states.md) — the design rules for the placeholder content that fills persistent layout slots.
- [layout-shift.md](./layout-shift.md) — when the chrome is rendered but its dimensions change.
