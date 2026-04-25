# Video frame analysis with ffmpeg

The unique technique this skill teaches: turn a 5-second screen recording into a structured timeline of "what changed when", so you can characterise each visible flash precisely instead of guessing from a slow-motion replay.

## Tools required

- `ffmpeg` — frame extraction, scene detection, format conversion.
- `ffprobe` — video metadata.
- An image viewer that loads single PNGs (Claude Code's `Read` tool, your IDE's preview, `open` on macOS).

Install: `brew install ffmpeg` (macOS), `apt install ffmpeg` (Debian/Ubuntu), or your distro equivalent. ffprobe ships with ffmpeg.

## Recipe 1: probe the video

Always start with metadata — frame rate matters for picking extraction density.

```bash
ffprobe -v error \
  -show_entries stream=width,height,r_frame_rate,duration,nb_frames \
  -show_entries format=duration \
  -of json input.mp4
```

Output sample:
```json
{
  "streams": [{ "width": 1920, "height": 1080, "r_frame_rate": "240/1", "duration": "7.85", "nb_frames": "235" }]
}
```

Notes:

- **240 fps** is common for high-quality screen capture — you have lots of frames per visible transition.
- **30 fps** is typical for `Cmd-Shift-5` defaults — fewer frames, may need scene detection rather than dense sampling to find transitions.
- A 5-second video at 30 fps = 150 frames. At 240 fps = 1200 frames. Don't extract them all.

## Recipe 2: scene detection (find the flashes automatically)

ffmpeg's `select=gt(scene,N)` filter outputs only frames where the pixel-difference from the previous frame exceeds `N`. Threshold tuning:

- `0.03` — catches subtle layout shifts (a panel appearing). Use this first.
- `0.10` — catches major scene changes only (most of the screen content swapped).
- `0.30` — only completely different scenes.

```bash
ffmpeg -i input.mp4 -vf "select='gt(scene,0.03)',showinfo" -vsync vfr -f null - 2>&1 \
  | grep "showinfo.*pts_time" \
  | awk -F'pts_time:' '{print $2}' \
  | awk '{print $1}'
```

Output: a list of timestamps (in seconds) where significant pixel change occurred. Each is a candidate flash point.

Sample output for a channel-creation flash:
```
2.779789
3.013122
5.279789
```

Three transitions. If two are within 0.5s of each other, that's likely one user action that triggered multiple cascading re-renders — characterise both before/after pairs.

## Recipe 3: extract before/after for each transition

For each timestamp from scene detection, grab one frame ~50ms before and one frame at the transition:

```bash
TIMESTAMPS="2.779789 3.013122 5.279789"

mkdir -p frames && rm -f frames/*.png 2>/dev/null

for t in $TIMESTAMPS; do
  before=$(echo "$t - 0.05" | bc)
  ffmpeg -ss $before -i input.mp4 -frames:v 1 -q:v 2 \
    "frames/t${t}_before.png" -hide_banner -loglevel error
  ffmpeg -ss $t -i input.mp4 -frames:v 1 -q:v 2 \
    "frames/t${t}_after.png" -hide_banner -loglevel error
done

ls frames/
```

`-q:v 2` is high-quality JPEG/PNG (lower is better, 1-31 scale). Always use `-q:v 2` for diagnostic frames — you'll be reading text in them.

## Recipe 4: dense extraction (when scene detection misses subtle changes)

If scene detection returns nothing but the user reports flashes, sample at a fixed rate:

```bash
ffmpeg -i input.mp4 -vf "fps=20" "frames/frame_%04d.png" -hide_banner -loglevel error
```

20 fps = one frame every 50ms. For a 5-second video that's 100 frames. Walk through them in pairs and look for visual deltas.

## Recipe 5: crop a specific region for fine-grained inspection

When you suspect a specific element (e.g. a tab strip near the top, a sidebar on the left), crop to it:

```bash
# Crop top 80px, full width — for inspecting a header/tab strip across frames
ffmpeg -ss $t -i input.mp4 -frames:v 1 -vf "crop=in_w:80:0:0" \
  -q:v 1 "tabstrip_t${t}.png" -hide_banner -loglevel error

# Crop URL bar (rough — adjust offsets per recording)
ffmpeg -ss $t -i input.mp4 -frames:v 1 -vf "crop=900:30:200:5" \
  -q:v 1 "urlbar_t${t}.png" -hide_banner -loglevel error
```

Cropped frames are much smaller and let you compare specific UI regions side-by-side without the rest of the screen as noise.

## Recipe 6: side-by-side compare for the writeup

To produce a single image showing before/after side by side (great for PR descriptions):

```bash
ffmpeg -i frame_before.png -i frame_after.png \
  -filter_complex "[0]pad=iw*2:ih[bg];[bg][1]overlay=w" \
  comparison.png
```

## Reading frames in Claude Code

The `Read` tool can load PNGs directly. Each frame becomes available as an image observation in the agent's context. To analyse: load before and after for the same transition timestamp, describe what changed in prose. Categorise the change against the [core.md](../core.md) anti-pattern list.

## Frame-by-frame walkthrough is faster than re-watching

Once you have 6-12 PNGs (3-4 transitions × 2 frames each + a few establishing shots), reading them as still images is *much* faster than re-watching the video. You can also share the frames in PR descriptions / bug reports without forcing the reviewer to scrub a video.

## Output organisation

Suggested layout for a diagnostic session:

```
/tmp/render-stability-<bug-name>/
├── input.mp4                    # original video (or symlink)
├── timestamps.txt               # output of scene detection
├── frames/
│   ├── t2.78_before.png
│   ├── t2.78_after.png
│   ├── t3.01_before.png
│   ├── t3.01_after.png
│   └── …
├── crops/                       # optional — region-specific compares
│   ├── tabstrip_t2.78_before.png
│   └── …
└── findings.md                  # writeup: each transition + which anti-pattern
```

Keep it under `/tmp/` (gitignored, ephemeral) unless you want the frames as PR attachments — then move to `<repo>/.ai/plans/<plan>/` and commit the relevant ones.
