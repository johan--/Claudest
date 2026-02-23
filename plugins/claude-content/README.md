# claude-content

Content creation and processing tools for Claude Code. Six skills covering image generation, video manipulation, social media formatting, and audio extraction.

## Why

Most content workflows involve the same small set of operations applied repeatedly: compress this for web, convert to a different format, make it fit Instagram, extract the audio, generate a thumbnail. The individual FFmpeg commands are tedious to remember and easy to get wrong — the right CRF for H.265, the palette generation pipeline for GIF quality, the aspect ratio math for Reels. These skills encode the correct defaults so you don't have to look them up, and handle multi-step operations (trim + resize + convert) as single commands rather than intermediate-file chains.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-content@claudest
```

**Requirements:**
- `ffmpeg` and `ffprobe` — required for all video and audio skills
- `GEMINI_API_KEY` environment variable and `uv` — required for image generation only

## Skills

### generate-image

Generate and edit images using Google's Gemini Pro Image API. Handles three modes: text-to-image (describe what you want), image-to-image (provide a source image and editing instructions), and multi-reference composition (combine elements from multiple source images with a prompt).

Triggers on: "generate an image", "create a picture", "make me a logo", "edit this image", "remove the background", "change the style", "combine these images", "add text to image", "make a sticker", "product mockup".

### compress-video

Compress video using quality-based or size-based encoding. Profiles the source file first, then applies CRF encoding to hit a visual quality target, or 2-pass encoding to hit a specific file size. Selects codec and settings based on the source and target.

Triggers on: "compress this video", "reduce file size", "make this video smaller", "optimize for web", "compress to under X MB", "encode with H.265", "re-encode this video".

### convert-video

General-purpose video manipulation: format conversion, trim, speed adjustment, slow motion, timelapse, frame extraction, resize, rotate, flip, remux. Multi-operation requests are chained into a single ffmpeg invocation — no intermediate files, no quality loss from multiple encode passes.

Triggers on: "convert this video", "change format to mp4", "trim from X to Y", "cut the first X seconds", "speed up this video", "slow motion", "timelapse", "extract frames", "resize video", "rotate video", "flip video".

### make-gif

Convert a video clip to a high-quality animated GIF using the mandatory 2-pass palette workflow. `palettegen` analyzes the clip to build an optimal 256-color palette; `paletteuse` renders with it. Single-pass GIF always produces banding and color artifacts. This doesn't.

Triggers on: "make a GIF", "convert to GIF", "create a GIF from this video", "export as GIF", "turn this clip into a GIF", "gif this".

### share-social

Prepare video for platform-specific upload requirements: correct aspect ratios, resolutions, bitrates, and container settings. Presets for Instagram Reels, YouTube Shorts, TikTok (9:16), square posts (1:1), Twitter, Facebook, and LinkedIn.

Triggers on: "optimize for Instagram", "YouTube Shorts format", "make it 9:16", "TikTok format", "Reels format", "prepare for social media", "encode for Twitter", "crop for portrait".

### extract-audio

Rip the audio track from any video file, with format selection based on use case: FLAC for lossless archival, MP3 VBR for transparent compression at small file sizes, AAC for maximum device compatibility.

Triggers on: "extract audio", "get the mp3", "strip audio from video", "rip audio", "save audio from video", "get the soundtrack", "pull the audio track", "export audio".

## License

MIT
