# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-03-10

### Changed
- Patch version bump by auto-version hook after docs refresh commit

## [0.4.0] - 2026-03-10

### Changed
- Refresh README with current version badge and add CHANGELOG entries through v0.4.0

## [0.3.1] - 2026-02-28

### Added
- Structured prompting guide for image-to-image editing covering failure modes: color label drift, same-color swap targets, Gemini camera move limitation, multi-pass editing, and base scene contamination
- Fashion and garment editing patterns: base image selection, garment swap prompts, and texture rendering guidance
- Frame extraction instructions using ffmpeg scene detection for pulling video references

## [0.3.0] - 2026-02-27

### Changed
- Upgrade generate-image to dual model tier architecture: Nano Banana (default, fast, extended aspect ratios up to 8:1 panoramic, thinking mode, Google Search grounding) and Nano Banana Pro (higher quality, up to 2K resolution)

## [0.2.1] - 2026-02-22

### Fixed
- Repair ffmpeg skill suite (compress-video, convert-video, make-gif, share-social, extract-audio) to correct implementation issues

### Changed
- Rename all skills to verb-first naming convention

## [0.1.0] - 2026-02-22

### Added
- Initial claude-content plugin with six content creation skills
- generate-image: text-to-image, image-to-image, and multi-reference composition using Gemini API
- compress-video: quality-based (CRF) and size-based (2-pass) video compression
- convert-video: format conversion, trim, speed, resize, rotate, frame extraction, and chained multi-operation ffmpeg invocations
- make-gif: high-quality GIF export using mandatory 2-pass palette workflow (palettegen + paletteuse)
- share-social: platform-specific video encoding presets for Instagram Reels, YouTube Shorts, TikTok, Twitter, Facebook, and LinkedIn
- extract-audio: audio extraction with format selection (FLAC, MP3 VBR, MP3 CBR, AAC, WAV, stream copy)
