---
name: extract-learnings
description: >
  Persist learnings to memory or maintain existing memories. Triggers on
  "extract learnings", "save this for next time", "remember this pattern",
  "consolidate memories", "dream", "clean up memories".
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(python3:*)
  - Bash(git:*)
  - Bash(date:*)
  - AskUserQuestion
---

## Memory Hierarchy

Learnings are placed based on scope, persistence needs, and attention priority. Closer to Layer 0 = loaded every session = more agent attention.

| Layer | File | When Loaded | Purpose |
|-------|------|-------------|---------|
| 0 | `~/.claude/CLAUDE.md` | Every session, all projects | Universal behavioral preferences |
| 1 | `<repo>/CLAUDE.md` | Every session, this project | Project architecture, conventions, gotchas |
| 2 | `~/.claude/projects/.../memory/MEMORY.md` | Every session, agent-managed | Evolving notes, version history, working knowledge |
| 3 | `memory/*.md` topic files | On-demand, when relevant | Detailed reference too long for Layer 2 |
| Meta | Suggest new skill/command | N/A | Repeatable workflow patterns deserve automation |

### Placement Decision Tree

For each candidate learning, ask in order:

1. **Project-independent behavioral preference?** → Layer 0 (`~/.claude/CLAUDE.md`)
   Example: "Always use bun instead of npm", "Never auto-commit without asking"

2. **Project-specific technical knowledge?** → Layer 1 (`<repo>/CLAUDE.md`)
   Example: "FTS cascade: FTS5 → FTS4 → LIKE", "Always bump version in two files"

3. **Concise working note the agent should see every session?** → Layer 2 (`MEMORY.md`)
   Example: "v0.5.1: added Python 3.7 compat", "User prefers conventional commits"

4. **Detailed reference too long for Layer 2?** → Layer 3 (topic file in `memory/`)
   Example: Deep debugging guide, complex architecture notes, long reference tables

5. **Repeatable workflow pattern?** → Meta: suggest creating a skill or command
   Example: "We keep doing X manually → propose a skill for it"

## Context Gathering Tools

Reuse the recall-conversations tools when retrieval from prior sessions is needed.

### recent_chats

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recall-conversations/scripts/recent_chats.py --n 10
```

Returns markdown-formatted sessions with exchange headers, timestamps, and project paths. Use `--format json` for structured filtering.

### search_conversations

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recall-conversations/scripts/search_conversations.py --query "keyword"
```

Returns matching sessions ranked by relevance (BM25 when FTS5 available). Use `--format json` for structured result parsing.

For full option catalogs, load `${CLAUDE_PLUGIN_ROOT}/skills/recall-conversations/references/tool-reference.md`. Both scripts default to markdown (token-efficient for synthesis). Use `--format json` when filtering or counting sessions programmatically.

## Mode Detection

This skill has two modes. Detect which one applies before proceeding.

**Capture mode** — the user has specific learnings to save from the current or recent conversations. Triggered by: "save this", "remember this", "extract learnings", "add to memory", explicit learning content in the conversation.

**Consolidation mode** — the user wants to maintain, clean up, or review existing memories. Triggered by: "consolidate", "dream", "autodream", "clean up memories", "prune", "maintain memories", "review my memories", or when a SessionStart hook nudges that consolidation is overdue.

If ambiguous, use AskUserQuestion: "Are you looking to save something specific from this session, or maintain/clean up your existing memories?"

---

## Capture Workflow

Four stages: **Gather → Analyze → Propose → Execute**. Never skip the proposal stage.

### Stage 1: Orient & Gather

Read existing memory state first, then gather new signal.

1. **Read existing memories** — Read MEMORY.md and skim topic file names (Glob `memory/*.md`). This builds a model of what is already known, so Stage 2 can identify genuine gaps rather than rediscovering known information.

2. **Gather new signal** — deduce intent from available context:

- **Current conversation signal** ("save this for next time", "remember this pattern"): Source material is already in context. Do not fetch past sessions.

- **Past session signal** ("we figured out that...", "remember when we..."): Use `search_conversations.py` or `recent_chats.py` to retrieve that context. Extract substantive keywords to build the query.

- **Broad extraction request** ("extract learnings from recent sessions"): Use `recent_chats.py --n 10` to gather recent context.

- **Ambiguous intent**: Use `AskUserQuestion` to clarify what to extract and from where. Do not guess.

Exit Stage 1 when existing memory state is loaded and at least one source of candidate learnings is in context. If ambiguous intent remains unresolved after one `AskUserQuestion` round, stop and report.

### Stage 2: Analysis & Distillation

Identify how the knowledge base should change given the gathered signal. For each piece of new information, classify:

- **FILL GAP** — important knowledge with no existing entry
- **UPDATE** — something changed since an existing memory was written
- **NOISE** — one-off incident with no recurring pattern, or already captured

Only FILL GAP and UPDATE produce candidates. Discard NOISE.

**Generalization rule:** When you find a specific incident (a debugging session, a one-time fix, a configuration discovery), ask: is there a general principle behind this? Record the principle, not the incident. The incident is evidence; the principle is the learning.

- Incident-shaped (avoid): "We spent 30 minutes debugging why the hook failed — CLAUDECODE env var was blocking nested calls."
- Principle-shaped (prefer): "Strip CLAUDECODE env var before spawning claude -p subprocesses — the guard prevents nesting but only matters for interactive sessions."

For each candidate, determine: the learning as a reusable principle (1-2 sentences), the target layer (via the decision tree), and the target section within that file.

Limit to 3-7 candidates per invocation. If more surface, rank by impact and present the top set.

### Stage 3: Placement Proposal

This is the critical stage. Never write without explicit approval.

1. **Read current state** of all target files that have candidates aimed at them. Only read files with pending changes.

2. **Check for duplicates** — scan target files for existing content covering the same concept. If already captured (even in different words), skip it and note the duplicate.

3. **Present the proposal** — for each candidate, use this format:
```
   ### [ACTION] Learning: <one-line summary>
   **Target:** <file path> → <section name>
   **Rationale:** <why this layer, why this section>

   ```diff
   + <lines to add>          ← for ADD actions
   - <old line>              ← for EDIT actions (show what changes)
   + <new line>
   ```
```
   Actions: ADD (new entry), EDIT (update existing entry), REMOVE (delete stale entry).

4. **Layer 0 extra gate** — if any learning targets `~/.claude/CLAUDE.md`, add an explicit warning: "This will be added to your global instructions loaded in every session across all projects. Confirm?"

5. **MEMORY.md line check** — read the target MEMORY.md and count lines. If line count exceeds 170, identify the lowest-value entries currently in MEMORY.md and suggest specific demotions to topic files (Layer 3) or removals to make room. Do not just warn — propose what to move.

6. **Get approval** — use `AskUserQuestion` with options:
   - "Approve all" — apply all proposed changes
   - "Approve selectively" — let user pick which learnings to apply
   - "Reject and redirect" — user wants changes placed differently

### Stage 4: Execution

Apply approved edits:

- **Existing files** (Layers 0-2): Use `Edit` to insert at the target section. Preserve existing structure and formatting.
- **New topic files** (Layer 3): Use `Write` to create `memory/<topic>.md`. Link from MEMORY.md if appropriate.
- **Edits to existing entries**: Use `Edit` to update the specific content.
- **Removals**: Use `Edit` to remove the entry. If removing a topic file entirely, also remove its pointer from MEMORY.md.
- **Skill suggestions** (Meta): Describe the proposed skill and let the user decide.

Output a summary table:

```
| Learning | Action | Target | Status |
|----------|--------|--------|--------|
| "Always use bun" | ADD | ~/.claude/CLAUDE.md | Applied |
| "FTS cascade order" | EDIT | repo CLAUDE.md | Updated |
| "Stale Express ref" | REMOVE | memory/api-stack.md | Removed |
```

---

## Consolidation Workflow

Four stages: **Orient → Gather Signal → Maintain → Propose & Execute**. Uses the same proposal format and approval gates as capture mode.

### Stage 1: Orient

Build a complete picture of current knowledge state before looking for changes.

1. **Read all memory files** — Read MEMORY.md, then read every topic file in `memory/`. Note: file count, total content size, any obvious organizational issues (near-duplicate files, orphaned entries).

2. **Read CLAUDE.md files** — Read both `~/.claude/CLAUDE.md` and `<repo>/CLAUDE.md` to understand what's already in higher-priority layers.

3. **Scan recent git activity:**
```bash
git log --oneline -20
```
Note significant changes (new features, refactors, dependency changes) that may not be reflected in memories.

4. **Queue verification checks** — for each memory that names a specific file path, function, class, or CLI flag, note it for codebase cross-reference in Stage 2.

Exit Stage 1 when all existing memories are loaded and verification targets are queued.

### Stage 2: Gather Signal

Search for changes worth reflecting in the knowledge base. This is hypothesis-driven — orient first, then search narrowly for suspected signals.

1. **Codebase cross-reference** — for each queued verification target from Stage 1, check whether the referenced entity still exists:
   - File paths: use Glob
   - Function/class names: use Grep
   - Flag any memory where the referenced entity is missing, renamed, or fundamentally changed. These are contradiction candidates.

2. **Recent session scan** — use `recent_chats.py --n 10` to pull recent sessions. Scan for:
   - User corrections or redirections ("don't do X", "actually we should Y")
   - Architectural decisions and their rationale
   - Recurring patterns across multiple sessions (same topic discussed twice = signal)
   - Information that contradicts or supersedes existing memories

3. **Git log diff** — compare git log findings (Stage 1.3) against existing memories. Look for shipped changes not reflected: dependency swaps, major refactors, new conventions, removed features.

4. **Date scan** — scan all existing memory files for relative date patterns: "yesterday", "last week", "today", "this morning", "recently", "just now". These need conversion to absolute dates.

Exit Stage 2 when all verification checks are complete and signal sources are gathered.

### Stage 3: Maintain

Classify all findings into maintenance actions. For each finding:

- **CONTRADICT** — existing memory conflicts with codebase state or newer information → propose EDIT or REMOVE
- **STALE** — memory references something that no longer exists → propose REMOVE or EDIT
- **DATE FIX** — relative date that should be absolute → propose EDIT with converted date
- **MERGE** — two entries cover the same topic → propose consolidating into one
- **FILL GAP** — important knowledge from recent sessions not yet captured → propose ADD (apply the generalization rule from Capture Stage 2)
- **PRUNE INDEX** — MEMORY.md is over 170 lines, or has pointers to low-value entries → propose demotion to topic files or removal

Apply the same generalization rule as capture mode: record principles, not incidents.

### Stage 4: Propose & Execute

Use the same proposal format as Capture Stage 3, with all action types (ADD, EDIT, REMOVE). Group by action type for readability:

```
CONSOLIDATION REPORT
────────────────────
Contradictions fixed: N
Stale entries removed: N
Dates converted: N
Entries merged: N
New learnings added: N
Index entries pruned: N
```

Then present each proposed change with the standard diff format. Get approval via `AskUserQuestion` with the same options as capture mode.

After executing approved changes, write a consolidation marker to the same directory as MEMORY.md. Use the `Bash` tool to get the timestamp (`date -u +%Y-%m-%dT%H:%M:%SZ`) and use the `Write` tool to create `.last-consolidation` with that ISO timestamp as its content.

---

## Content Quality Rules

Every candidate must pass these filters before being proposed:
- Would the agent benefit from knowing this in future sessions?
- Is it condensed to the minimum needed to be useful?
- Is it placed at the right layer (not too broad, not too narrow)?
- Does the target file not already contain this knowledge?
- Is it stated as a reusable principle, not a session-specific incident?

### Examples of passing

- Commands or workflows discovered through trial and error
- Non-obvious gotchas that caused debugging time
- Architectural decisions and their rationale
- Behavioral corrections from the user ("don't do X", "always do Y")
- Configuration quirks not obvious from reading code
- Package/module relationships not obvious from imports
- Version history milestones

### Examples of failing

- Information obviously readable from the code itself
- Generic programming best practices ("write tests", "use meaningful names")
- One-off bug fixes with no recurring pattern
- Verbose explanations — condense to a one-liner or skip
- Content already captured in the target file (semantic dedup)
- Temporary state or session-specific context
- Speculative conclusions not verified against the codebase
- Incident reports without a generalizable principle
