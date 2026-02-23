---
name: make-gif
description: >
  This skill should be used when the user asks to "make a GIF", "convert
  to GIF", "create a GIF from this video", "export as GIF", "turn this
  clip into a GIF", "make an animated GIF", or "gif this".
allowed-tools:
  - Bash(ffprobe:*)
  - Bash(ffmpeg:*)
  - AskUserQuestion
---

# Video GIF

Convert a video clip to a high-quality GIF using the mandatory 2-pass palette workflow.

Single-pass GIF always produces banding and color artifacts. The palettegen → paletteuse pipeline analyzes the actual clip to build an optimal 256-color palette, then renders with it. Never skip this.

## Process

### 1. Gather parameters

Ask for any not already provided in the request:
- **Start time** — default `0`
- **Duration or end time** — required; warn if >30s (file size grows rapidly)
- **Width** — default `480`px; height auto-calculated to preserve aspect ratio
- **FPS** — default `15`; higher = smoother + larger file

If the user asks about aspect ratio or the source has unusual dimensions, probe first:
```bash
ffprobe -v quiet -print_format json -show_streams "$INPUT" | \
  python3 -c "import json,sys; s=[s for s in json.load(sys.stdin)['streams'] if s['codec_type']=='video'][0]; print(s['width'], 'x', s['height'])"
```

### 2. Build the 2-pass command

**Pass 1 — generate optimized palette:**
```bash
ffmpeg -ss $START -t $DURATION -i "$INPUT" \
  -vf "fps=$FPS,scale=$WIDTH:-1:flags=lanczos,palettegen=stats_mode=full" \
  /tmp/palette_$$.png -y
```

**Pass 2 — render GIF using palette:**
```bash
ffmpeg -ss $START -t $DURATION -i "$INPUT" -i /tmp/palette_$$.png \
  -lavfi "fps=$FPS,scale=$WIDTH:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5" \
  "$OUTPUT" -y
```

Use `$$` (shell PID) in the palette temp path to avoid collisions with concurrent runs.

### 3. Confirm before running

Show the full 2-pass command and estimated output path. Add a size warning if `duration × fps` is large (rough heuristic: >20s at 15fps at 480px → likely >10MB).

### 4. Run both passes, then clean up

```bash
rm -f /tmp/palette_$$.png
```

Report output path and file size.

## Key Decisions

- `stats_mode=full` on palettegen analyzes the entire clip — not just the first frame — for better palette coverage across motion.
- `dither=bayer:bayer_scale=5` is the sweet spot for photographic content. Use `dither=none` for flat-color content (illustrations, slides, screen recordings with solid backgrounds).
- `-ss` placed **before** `-i` uses container-level fast seek. Apply to both passes for consistent start points and dramatically faster seeks on long source files.
- `flags=lanczos` on scale gives sharper downsampling than the default `bilinear`.
- To control loop count, add `-loop $N` to pass 2: `0` = infinite, `1` = play once, `2` = play twice.
