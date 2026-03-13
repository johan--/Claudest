---
name: create-output-style
description: Generate a persona-based output style file via guided interview
user-invoked: true
argument-hint: "[name] - or leave empty to interview"
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Glob
---

Generate concise, effective output style files for `~/.claude/output-styles/`. Styles work by shifting the model's generation distribution through persona activation, not through rules or ban lists. Shorter styles produce more coherent behavioral shifts.

## Phase 0: Requirements

Parse `$ARGUMENTS` for name hints. Use AskUserQuestion to gather requirements adaptively.

### Round 1 (always)

Ask three questions in a single AskUserQuestion call:

1. **Style type** — options: "Character/Persona" (fictional archetype like Zen Master, noir detective), "Personal Voice" (match a specific person's writing style), "Coding Interaction" (change how Claude collaborates on code). This determines the generation path and `keep-coding-instructions` value.

2. **Audience** — who is the user talking to when this style is active? Options: "Yourself (notes, drafts)", "Technical peers", "Non-technical stakeholders", "General public". This shapes register and assumed context.

3. **One-sentence vibe** — free text. Ask: "Describe the voice you want in one sentence." This becomes the seed for persona synthesis.

### Round 2 (adaptive, based on style type)

**Character/Persona path:** Ask for 2-3 adjectives or a reference point ("like X but Y"). Enough to synthesize the persona directly.

**Personal Voice path with writing samples:** If `$ARGUMENTS` contains file paths or the user provided samples, read them. Extract: register (formal/casual/mixed), sentence cadence (short/varied/long), favorite rhetorical moves (questions? lists? analogies? direct assertions?), vocabulary field (technical/plain/literary). Synthesize a persona description internally — do not dump the analysis to the user.

**Personal Voice path without samples:** Ask two questions: (1) "What should this voice NOT sound like?" with options like "Corporate/formal", "Casual/chatty", "Academic/dense", "Default Claude". (2) "Paste a short paragraph of writing you admire (yours or someone else's)."

**Coding Interaction path:** Ask: "What's your ideal pair programmer like?" with options: "Terse — just the code, minimal explanation", "Educational — explains choices as we go", "Collaborative — asks before deciding", "Opinionated — makes strong recommendations".

### Round 3 (Personal Voice with samples only)

Present the synthesized persona back in 1-2 sentences. Ask: "Does this capture your voice?" with options: "Yes, use this", "Close but adjust: [free text]", "No, try again with different emphasis".

Proceed to Phase 1 when persona direction is established.

## Phase 1: Generate

Read `${CLAUDE_PLUGIN_ROOT}/skills/create-output-style/references/style-architecture.md` for the generation framework. Review the example matching the current style type for target format and density:

- Character/Persona: `${CLAUDE_PLUGIN_ROOT}/skills/create-output-style/examples/zen-minimalist.md` (~60 tokens, persona + anchors only)
- Personal Voice: `${CLAUDE_PLUGIN_ROOT}/skills/create-output-style/examples/whiteboard-voice.md` (~90 tokens, persona + anchors + exemplar phrases, `keep-coding-instructions: false`)
- Coding Interaction: `${CLAUDE_PLUGIN_ROOT}/skills/create-output-style/examples/direct-pair.md` (~80 tokens, collaboration-mode persona, `keep-coding-instructions: true`)

Compose the output style file following this structure:

1. **Frontmatter** — `name`, `description` (for /config picker), `keep-coding-instructions` (true for coding styles, false for writing/character styles).

2. **Persona sentence** (~40 tokens) — Activate the right neighborhood of style-space. For characters, use the archetype. For personal voice, use the synthesized writing posture. For coding styles, describe the collaboration mode.

3. **Tonal/thematic anchors** (2-4 sentences, ~60 tokens) — Narrow within the persona's neighborhood. Constrain register, cadence, structural preferences. Write as positive guidance ("favor X"), not negative rules ("don't do Y").

4. **Exemplar phrases** (optional, ~50 tokens) — Only for personal voice styles where samples were provided. Quote 2-3 short phrases from the samples that demonstrate target cadence and register.

5. **Structural constraints** (optional, 1-2 sentences, ~30 tokens) — Only when a specific structural habit is critical to the voice (e.g., "one idea per paragraph", "lead with the conclusion"). Omit if persona + anchors are sufficient.

Token budget: soft target 200, hard max 400. If over 400, cut structural constraints first, then exemplar phrases. Never cut persona or anchors.

Never include ban lists. Never list forbidden words or phrases. The persona and anchors handle distribution shifting; bans only suppress surface tokens while the underlying patterns persist.

## Phase 2: Deliver

### Check for collisions

```
Glob: ~/.claude/output-styles/*.md
```

If a file with the same slug exists, ask whether to overwrite or rename.

### Write the file

Generate a URL-safe slug from the style name (lowercase, hyphens for spaces). Write to `~/.claude/output-styles/[slug].md`.

If `~/.claude/output-styles/` does not exist, create it.

### Explain choices

Briefly note:
- The persona and why it was chosen
- `keep-coding-instructions` value and why
- How to activate: Settings > Output style, or `/config` > Output style

## Phase 3: Evaluate

Check the generated file against these criteria:

| Check | Pass condition |
|-------|---------------|
| Token count | Body under 400 tokens (warn if over 200) |
| No ban lists | No "don't use", "never say", "avoid the word" patterns |
| Frontmatter valid | name, description, keep-coding-instructions all present |
| Persona present | First sentence establishes voice identity |
| Anchors present | At least 2 narrowing sentences after persona |

If any check fails, fix inline and note the correction. Deliver the final path and activation instructions.
