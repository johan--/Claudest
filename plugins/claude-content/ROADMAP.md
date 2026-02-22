# claude-content Roadmap

## Future Skills

### FFmpeg — Next Pass

**`video-concat`**
Join multiple video clips end-to-end. Two code paths: concat demuxer (same codec, no re-encode, instant) vs. concat filter (re-encode, handles mixed formats/resolutions). Common request: "merge these clips", "join into one file", "combine these videos in order". Needs user to specify clip order and whether re-encoding is acceptable.

**`video-subtitle`**
Burn SRT or ASS subtitles into video using the `subtitles` filter (`-vf "subtitles=file.srt"`). Common for accessibility, social media captions, translated content. Flag syntax is unintuitive on macOS/Windows (path escaping). Skill value: chooses between soft subs (copy stream) vs. hard subs (burn in), handles font/style overrides for ASS.

**`video-watermark`**
Overlay a text or image logo on video. Text: `drawtext` filter (font, size, position, color, opacity, timestamp/timecode). Image: `overlay` filter (positioning, transparency via `[0:v][1:v]` mapping). Common for branding, screen recordings, demo videos. High skill-worthiness: `drawtext` has ~20 options and the position math (e.g., `x=W-w-10:y=H-h-10` for bottom-right) is non-obvious.
