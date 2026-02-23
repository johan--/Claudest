---
name: extract-audio
description: >
  This skill should be used when the user asks to "extract audio",
  "get the mp3", "strip audio from video", "rip audio", "save audio
  from video", "convert to audio", "get the soundtrack", "pull the
  audio track", "save as mp3", "export audio", or "separate audio
  from video".
allowed-tools:
  - Bash(ffprobe:*)
  - Bash(ffmpeg:*)
  - AskUserQuestion
---

## Format Decision Tree

| User wants | Format | Flags | Why |
|------------|--------|-------|-----|
| Music, archive quality | FLAC | `-c:a flac` | Lossless, no quality loss |
| Music, small + transparent | MP3 VBR | `-c:a libmp3lame -q:a 0` | ~200kbps avg, perceptually lossless |
| Podcast / voice | MP3 128k CBR | `-c:a libmp3lame -b:a 128k` | Sufficient for speech, universally compatible |
| Mobile / streaming | AAC 192k | `-c:a aac -b:a 192k` | Better than MP3 at equivalent bitrate |
| DAW / editing | WAV | `-c:a pcm_s16le -ar 44100` | No encoding loss, widest DAW support |
| Source already target format | Copy | `-c:a copy` | No re-encode, instant, lossless |

## Process

### 1. Probe audio streams

```bash
ffprobe -v quiet -print_format json -show_streams "$INPUT" | \
  python3 -c "
import json, sys
streams = [s for s in json.load(sys.stdin)['streams'] if s['codec_type']=='audio']
for i, s in enumerate(streams):
    print(f'Stream {i}: {s[\"codec_name\"]} {s.get(\"bit_rate\",\"?\")} bps {s.get(\"channel_layout\",\"?\")}')
"
```

### 2. Determine format

Apply the decision tree above if the user didn't specify. If the source audio codec already matches the target, use `-c:a copy` to avoid transcoding.

If multiple audio streams exist, ask the user which to extract — or use `-map 0:a` to extract all. Once the user responds, apply `-map 0:a:N` (where N is the zero-based stream index they chose) or `-map 0:a` for all streams in the Phase 3 command.

### 3. Construct command

```bash
# General pattern (-vn drops the video stream entirely):
ffmpeg -i "$INPUT" -vn [FORMAT_FLAGS] "$OUTPUT"

# Examples:
ffmpeg -i video.mp4 -vn -c:a libmp3lame -q:a 0 audio.mp3        # MP3 VBR best quality
ffmpeg -i video.mp4 -vn -c:a libmp3lame -b:a 128k podcast.mp3   # MP3 128k CBR
ffmpeg -i video.mp4 -vn -c:a flac archive.flac                   # FLAC lossless
ffmpeg -i video.mp4 -vn -c:a aac -b:a 192k mobile.aac           # AAC
ffmpeg -i video.mp4 -vn -c:a pcm_s16le -ar 44100 edit.wav       # WAV for DAW
ffmpeg -i video.mp4 -vn -c:a copy original.m4a                  # Copy audio stream
```

### 4. Confirm and run

Show: detected source codec and bitrate, chosen output format, output path. Wait for approval, then run.

Report output file size and duration: `ffprobe -v quiet -show_format "$OUTPUT" | grep -E "duration|size"`

## Key Decisions

Preserve generation quality: avoid transcoding chains that degrade source fidelity. Each decision below is an application of this principle.

- **Lossy-to-lossy warning**: if the source is already lossy (MP3, AAC, OGG) and the user wants a different lossy format, warn them that re-encoding degrades quality. Recommend keeping the source format or using `-c:a copy` where container compatibility allows.
- For files >1 hour, ask whether the user wants the full file or a specific range — trimming can be added with `-ss` and `-to` before `-vn`.
- M4A vs AAC: AAC is the codec, M4A is the container. Use `.m4a` extension for Apple device compatibility; use `.aac` for a raw stream.
