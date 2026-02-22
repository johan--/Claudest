---
name: image-generation
description: >
  This skill should be used when the user asks to "generate an image", "create a
  picture", "make me a logo", "edit this image", "remove the background", "change the
  style", "combine these images", "add text to image", "style transfer", "make a
  sticker", "product mockup", or any image creation/manipulation request. Handles t2i
  (text-to-image), i2i (image-to-image editing), and multi-reference composition
  using Gemini Pro.
allowed-tools:
  - Bash(uv:*)
  - Read
  - AskUserQuestion
---

# Image Generation

Generate and edit images using Google's Gemini Pro Image API. Requires `GEMINI_API_KEY` environment variable and `uv` package manager.

## Workflow

1. **Understand** — Determine mode (t2i, i2i, multi-reference), gather parameters (aspect ratio, resolution, output path). Exit: mode and parameters are clear.
2. **Craft prompt** — Apply the prompting principles below to write the prompt. For t2i, use narrative prose. For i2i/multi-reference, use directive grammar with reference blocks. Exit: prompt is written and follows the relevant checklist.
3. **Confirm** — Show the user the exact prompt, input images (if any), resolution, and aspect ratio. Ask for confirmation. Exit: user approves.
4. **Generate** — Run the script with confirmed parameters. Exit: images are saved and displayed.
5. **Iterate** — Present results. Offer refinements (prompt tweaks, parameter changes, follow-up edits). Exit: user is satisfied or moves on.

## Default Output & Logging

When the user doesn't specify a location, save images to:
```
~/Documents/generated images/
```

Every generated image gets a companion `.md` file with the prompt used (e.g., `logo.png` → `logo.md`).

When gathering parameters (aspect ratio, resolution), offer the option to specify a custom output location.

---

## Core Prompting Principle

Describe scenes narratively, not as keyword lists. Gemini's language model parses prose with full semantic understanding — narrative prompts encode spatial relationships, mood, and intent that comma-separated tags cannot express. Tag-style prompts lose compositional meaning and produce generic results.

```
Bad:  "cat, wizard hat, magical, fantasy, 4k, detailed"

Good: "A fluffy orange tabby sits regally on a velvet cushion, wearing an ornate
       purple wizard hat embroidered with silver stars. Soft candlelight illuminates
       the scene from the left. The mood is whimsical yet dignified."
```

A useful formula: `[Subject] doing [Action] in [Context]. [Camera/Composition]. [Lighting]. [Style]. [Constraint].` Not every prompt needs every element — match detail to intent. If the user has a specific vision, be prescriptive (exact descriptions); if exploring, be open (general direction, let the model decide details). Ask if unclear.

Editing with reference images follows different principles — see [references/editing-guide.md](references/editing-guide.md).

---

## References

Load the relevant reference during prompt crafting (workflow step 2):

- [references/capability-patterns.md](references/capability-patterns.md) — mode-specific tips for photorealistic scenes, product photography, logos, stylized illustration, and grounding
- [references/editing-guide.md](references/editing-guide.md) — edit grammar, reference blocks, directive structure, image ordering, semantic masking, character consistency
- [references/style-reference.md](references/style-reference.md) — named aesthetics lexicon (film stocks, cameras, studios, artists, movements)

### Key Principles

Editing prompts direct changes rather than describing scenes. Point to what the model can see; describe only what it cannot. Base image goes last in `--input`; Gemini numbers images in reverse order.

Names invoke aesthetics directly — referencing "shot on Kodak Portra 400" produces its characteristic look more reliably than describing warm skin tones and pastel highlights.

---

## Configuration

### Aspect Ratios
1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9

### Resolutions
- **1K** (~1024px) — default, fast
- **2K** (~2048px) — high quality
- **4K** (~4096px) — maximum detail

**Defaults**: 1K resolution, batch 3, aspect ratio auto-detected from last reference image (or 1:1 if no images). Use 2K for higher quality requests, 4K only when high detail is explicitly needed (large prints, zoom-in).

---

## Script Usage

One unified script handles all modes: t2i, i2i, and multi-reference composition.

```bash
# Text-to-image (t2i)
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/generate.py --prompt "A serene mountain lake at dawn" --output landscape.png

# Image-to-image editing (i2i)
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/generate.py --prompt "Make it sunset colors" --input photo.png --output edited.png

# Multi-reference composition (up to 14 images)
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/generate.py --prompt "Combine the cat from image 1 with the background from image 2" --input cat.png --input background.png --output composite.png

# With options
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/generate.py --prompt "Logo for 'Acme Corp'" --output logo.png --aspect 1:1 --resolution 2K

# With Google Search grounding
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/generate.py --prompt "Current weather in Tokyo visualized" --output weather.png --grounding

# Batch generation (up to 4 images, 2 parallel requests)
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/generate.py --prompt "A cat in different poses" --output cat.png --batch 4
# Outputs: cat-1.png, cat-2.png, cat-3.png, cat-4.png
```

### Script Options

| Flag | Short | Description |
|------|-------|-------------|
| `--prompt` | `-p` | Image description or edit instruction (required) |
| `--output` | `-o` | Output file path (required) |
| `--input` | `-i` | Input image(s) for editing/composition (repeatable, up to 14) |
| `--aspect` | `-a` | Aspect ratio (auto-detects from last reference image, or 1:1) |
| `--resolution` | `-r` | Output resolution: 1K, 2K, or 4K (default: auto-detect or 1K) |
| `--grounding` | `-g` | Enable Google Search grounding |
| `--batch` | `-b` | Generate multiple variations: 1-4 (default: 1, runs 2 parallel max) |

### Auto-Resolution Detection

When editing images, the script automatically detects appropriate resolution from input dimensions:
- Input ≥3000px → 4K output
- Input ≥1500px → 2K output
- Otherwise → 1K output

Override with explicit `--resolution` flag.

### Auto Aspect Ratio Detection

When no `--aspect` flag is provided:
- **With reference images**: Detects from the **last** input image (closest supported ratio)
- **Without reference images (t2i)**: Defaults to 1:1

This matches typical editing workflows where the last image is the canvas being edited.

### Image Optimization

Large input images (>2048px) are automatically resized before sending to the API to prevent timeout errors. The script uses high-quality LANCZOS resampling to preserve detail during downscaling. Original files are never modified.

---

## Pre-Generation Checklist

**Before generating (t2i):**
- [ ] Narrative description (not keyword list)?
- [ ] Camera/lighting details for photorealism?
- [ ] Text in quotes, font style described?
- [ ] Aspect ratio appropriate for use case?

**Before editing (i2i / multi-reference):**
- [ ] Reference block at start of prompt labeling each image's role?
- [ ] Prompt directs rather than describes?
- [ ] Each directive (replace/match/keep) is its own sentence?
- [ ] Base image is last in `--input` list?
- [ ] When extracting/transferring elements: explicitly named each element rather than generic "outfit/object from image X"?
