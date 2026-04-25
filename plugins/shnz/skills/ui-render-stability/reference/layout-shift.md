# Layout shift (CLS)

The component is in both before and after frames, but at a different y-coordinate or with different dimensions, pushing siblings around. This is what Google's Cumulative Layout Shift (CLS) metric measures.

## Identifying it in frames

In your before/after pair:

- A button or panel is in both frames but at a different position.
- The content below or to the right of an element jumps when that element resizes.
- Text content appears to "settle" downward as web fonts load.
- An image area initially has zero height, then expands when the image arrives.

Distinct from [conditional-chrome.md](./conditional-chrome.md) (where elements mount/unmount) — here the element is present throughout but its size changed.

## Common causes

### Images without dimensions

```html
<img src="/photo.jpg" />        <!-- ❌ no width/height -->
<img src="/photo.jpg" width="800" height="600" />  <!-- ✅ reserves space -->
```

The img element has 0 height until the source loads. Content below shifts down when the image arrives.

### Web fonts swapping

`font-display: swap` (the common default) shows fallback fonts immediately, then swaps to the web font when it loads. The web font has different metrics → text reflows → layout shifts.

Fix: `font-display: optional` (use fallback if the web font isn't immediately ready), or pre-load the web font with `<link rel="preload">`. The Web Performance docs cover the trade-offs.

### Async-injected content

Ads, embeds, and async-loaded components push subsequent content down when they appear. Reserve their space:

```css
.ad-slot { min-height: 250px; }
```

### Auto-sizing containers

A container with `height: auto` resizes when its content arrives. If you know the expected dimensions, set a `min-height` matching the eventual size — even a generous overestimate is better than zero-then-real.

## Diagnosing in DevTools

Chrome / Edge DevTools → "Rendering" tab → enable **"Layout Shift Regions"**. Reproduce the interaction. Shifted regions flash blue for a moment.

Combine with **"Paint flashing"** to see what re-rendered. CLS without paint flashing = layout reflow without re-paint of the shifting element (rare but happens). Paint flashing without CLS = re-render but no shift (often fine, sometimes wasted).

## The element-in-place pattern

When a component must change size (e.g. an expandable panel), make the change explicit and animated rather than instant:

```css
.panel { transition: height 200ms ease-out; }
```

The user perceives the change as deliberate, not as a glitch. Caveat: animating `height` triggers layout on every frame; for production-critical paths, use `transform: translateY()` and absolute-positioned containers, or `content-visibility: auto`.

## Pairs with

- [conditional-chrome.md](./conditional-chrome.md) — when the element appears/disappears entirely rather than resizing.
- [skeleton-states.md](./skeleton-states.md) — when the issue is "real content's dimensions differ from skeleton's dimensions."
