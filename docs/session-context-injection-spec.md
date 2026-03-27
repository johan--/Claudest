# Session Context Injection Redesign — Spec

## Overview

Redesign the memory-context SessionStart injection from unbounded verbatim conversation dumps (5-17k tokens) to a precomputed structured summary (median 3k tokens) stored at Stop time. The injection uses an interleaved hybrid format: metadata header, structured extraction markers (decisions/open threads), first exchange, and last 3 exchanges with mid-truncated assistant responses. Full transcripts remain accessible via /recall-conversations.

## Key Themes

The core problem is that `build_context()` answers "what was said?" when it should answer "what matters now?" The current injection iterates all exchanges and dumps user + assistant text verbatim with no truncation or summarization. Assistant text dominates 7:1 over user text, with most of it being verbose explanations, tables, and code blocks that carry near-zero marginal signal over a compact summary.

The design separates "orientation context" (cheap, always injected) from "detailed recall" (expensive, available on demand). The summary is computed once at sync time and cached, making SessionStart injection a fast DB lookup rather than live content reconstruction.

Users are 50/50 between continuing the exact thread and pivoting to adjacent work. Both cases need: what's unfinished (open threads), what was decided (to avoid relitigation), and the handoff point (first + last exchanges). The verbatim dump works well for small sessions — the quality problem is purely size-driven, not signal-driven.

## Decisions and Positions

### Template format: interleaved hybrid
Header with metadata, structured extraction markers, first exchange pair, gap indicator, last 3 exchange pairs. The topic line is redundant with the first exchange and should be dropped. Template order optimizes for progressive disclosure — orient first, then detail.

### Token budget: 3k median, adaptive by exchange count
No hard cap. Exchange count naturally bounds the output. Short sessions (2-3 exchanges) inject everything verbatim. Medium sessions (4-10) use the full template. Large sessions (10+) still include first + last 3 exchanges with mid-truncation. Budget scales naturally because the number of exchanges in the template is fixed (max 4 exchange pairs).

### Assistant response truncation: 300 front + 600 back chars
Mid-truncation preserves the opening context and the conclusion/recommendation. User messages are kept verbatim (they're typically short). The "[... truncated ...]" marker indicates content was removed.

### Extraction heuristics: combined keyword + positional + detection
Multiple heuristic layers for structured marker extraction:

1. Keyword matching — scan for: "decided", "let's go with", "chose", "next step", "blocked on", "TODO", "skip", "instead of", "we should", "the plan is", "need to fix"
2. Positional extraction — last sentence of final assistant response + any bullet/numbered lists from it
3. Question detection — user messages ending with `?` in the last exchange that map to unanswered intents or "want me to..." / "should I..." responses
4. User intent prefixes — "let's", "can you", "I want", "we need to" in user messages
5. Negation tracking — "don't", "skip", "not X", "instead of" to capture explicit rejections
6. Code reference extraction — file paths (regex for `/path/to/file.ext` patterns) and function names from last few exchanges

### Storage: JSON source of truth + pre-rendered markdown
Store both `context_summary_json` (structured data for future template evolution) and `context_summary` (pre-rendered markdown for fast injection) on the `branches` table. JSON is the authoritative source; markdown is derived from it.

### Session selection: keep current algorithm, revisit later
The recency-based selection with exchange-count filtering is adequate for now. Branch-aware or file-overlap scoring can be added once structured markers exist and provide a relevance signal.

### Injection language: imperative with recall priming
The injected text uses imperative framing that primes Claude to proactively use /recall-conversations throughout the conversation — not just for this session's history, but whenever it senses relevant context from past conversations might exist. This turns recall from a passive fallback into an active retrieval habit.

### Migration: lazy fallback + background backfill
Old branches without cached summaries use a fallback: truncated last-3-exchanges built at inject time. The memory-setup.py SessionStart hook checks if backfill has been done (via a marker or schema version); if not, it spawns a background backfill process that computes summaries for all existing branches. This runs once per plugin install/update, then stays dormant.

## Template

```markdown
## Previous Session Context

### Session: {start_time} -> {end_time} (branch: {git_branch})
Modified: {files_modified[:6]}
Commits: {commits[:3]}
Tools: {tool_counts_summary}

### Key Signals
- [DECIDED] {extracted_decision}
- [OPEN] {extracted_open_thread}
- [NEXT] {extracted_next_step}
- [REJECTED] {extracted_rejection}

### First Exchange

**[{timestamp}] User:**
{first_user_message_verbatim}

**[{timestamp}] Assistant:**
{first_assistant_response_truncated_300_front_600_back}

[... {N} exchanges ...]

### Where We Left Off

**[{timestamp}] User:**
{last_3_user_message_verbatim}

**[{timestamp}] Assistant:**
{last_3_assistant_response_truncated_300_front_600_back}

[{exchange_count} total exchanges — proactively use /recall-conversations to retrieve relevant context from past conversations when the user references prior work, asks about decisions made earlier, or when you sense useful context from previous sessions would improve your response.]
```

## Schema Changes

Add to `branches` table:
- `context_summary TEXT` — pre-rendered markdown, ready for injection
- `context_summary_json TEXT` — structured JSON source of truth
- `summary_version INTEGER DEFAULT 0` — schema version for backfill detection

The JSON structure:

```json
{
  "version": 1,
  "topic": "first user message (120 chars)",
  "markers": [
    {"type": "DECIDED", "text": "...", "source_exchange": 5},
    {"type": "OPEN", "text": "...", "source_exchange": 12},
    {"type": "NEXT", "text": "...", "source_exchange": 12}
  ],
  "first_exchange": {
    "user": "full text",
    "assistant": "full text (pre-truncation)",
    "timestamp": "..."
  },
  "last_exchanges": [
    {
      "user": "full text",
      "assistant": "full text (pre-truncation)",
      "timestamp": "..."
    }
  ],
  "metadata": {
    "exchange_count": 12,
    "files_modified": [...],
    "commits": [...],
    "tool_counts": {...},
    "started_at": "...",
    "ended_at": "...",
    "git_branch": "..."
  }
}
```

## Implementation Plan

### Step 1: Schema migration
Add `context_summary`, `context_summary_json`, and `summary_version` columns to the `branches` table. Update `SCHEMA_CORE` in `db.py`. The auto-migration logic (delete + recreate on version mismatch) handles this, but for incremental migration add ALTER TABLE fallback.

### Step 2: Build the summarizer module
New file: `plugins/claude-memory/skills/recall-conversations/scripts/memory_lib/summarizer.py`

Functions:
- `extract_markers(messages) -> list[dict]` — runs all heuristic layers on stored messages
- `build_context_summary_json(branch_data, messages) -> dict` — assembles the full JSON structure
- `render_context_summary(summary_json) -> str` — renders JSON to injection-ready markdown with mid-truncation
- `compute_context_summary(cursor, branch_db_id) -> tuple[str, str]` — orchestrator that returns (markdown, json)

### Step 3: Integrate into sync_current.py
After branch metadata is computed and messages are stored, call `compute_context_summary()` and store results in the branch row. This runs in the background Stop hook, so latency is acceptable.

### Step 4: Rewrite build_context() in memory-context.py
Replace the message-iterating logic with a simple DB read of `context_summary`. Fallback: if `context_summary` is NULL (old branches), use the current truncated-last-3 approach.

### Step 5: Integrate into import_conversations.py
Add summary computation to the bulk import path so that re-imports also generate summaries.

### Step 6: Backfill mechanism
In memory-setup.py, after checking DB existence, check if backfill is needed (e.g., count branches where `summary_version = 0`). If significant count, spawn background process to compute summaries for existing branches.

## Open Questions

- Max count for structured markers (e.g., cap at 5 decisions + 5 open threads)?
- Should the backfill run incrementally (batch of 50 branches per session start) or all-at-once?
- Session selection algorithm improvements (branch-aware, file overlap scoring) — deferred, revisit after structured markers are available.

## Constraints and Boundaries

This spec does NOT cover: LLM-based summarization (all extraction is deterministic Python), changes to the recall-conversations skill, changes to the session selection algorithm, or changes to the sync_current.py Stop hook trigger mechanism. The existing schema for messages, sessions, and branch_messages is unchanged. The per-message `tool_summary` bug (0.03% populated) is a known issue but not in scope — branch-level `tool_counts` (96% populated) is the correct abstraction for injection.
