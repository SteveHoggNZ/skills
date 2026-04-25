# UI Render Stability (Codex adapter)

When the user describes a render-instability bug ("UI flashes", "screen flickers", "layout jumps", "tabs appear and disappear", "janky transition"), follow the methodology in [core.md](./core.md).

## Codex specifics

- **Tool mapping**: `bash` for ffmpeg frame extraction; image-viewer or your editor for inspecting PNGs; your edit function for applying the fix.
- **`ffmpeg` required** for the unique technique here (video → frame analysis). Install once: `brew install ffmpeg` (macOS) or distro equivalent.
- **Pair with [`agent-browser`](../agent-browser/)** for live reproduction. Pair with [`ui-state-debugging`](../ui-state-debugging/) when it's unclear whether the bug is wrong-state or unstable-render.

## At the start of every diagnostic

1. **Resolve the origin** of the app being debugged. Compute the slug per [reference/registry-format.md](./reference/registry-format.md).
2. **Read `.registry/<slug>.md`** if it exists — internalize the known conditional-chrome quirks for this app.
3. If there's a video, extract frames at scene changes via the ffmpeg recipe in [reference/video-frame-analysis.md](./reference/video-frame-analysis.md). Otherwise, ask the user to record one.
4. Walk the anti-pattern catalogue in [core.md](./core.md) and identify which one(s) match.

## At the end of every diagnostic

- **App-specific learnings** → `.registry/<slug>.md`.
- **Generic anti-patterns** → [reference/known-anti-patterns.md](./reference/known-anti-patterns.md).
- **Codebase-specific findings** → repo-local skill; see [`docs/COMPOSITION.md`](../../../../docs/COMPOSITION.md).
