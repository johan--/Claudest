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
  - Agent
---

## Memory Hierarchy

| Layer | File | Loaded | Purpose |
|-------|------|--------|---------|
| 0 | `~/.claude/CLAUDE.md` | Every session, all projects | Universal behavioral preferences |
| 1 | `<repo>/CLAUDE.md` | Every session, this project | Architecture, conventions, gotchas |
| 2 | `memory/MEMORY.md` (project dir) | Every session, agent-managed | Evolving notes, working knowledge |
| 3 | `memory/*.md` topic files | On-demand | Detailed reference too long for L2 |
| Meta | Suggest new skill/command | N/A | Repeatable workflow → automation |

Placement decision: project-independent preference → L0, project-specific technical → L1, concise working note → L2, detailed reference → L3, repeatable pattern → Meta.

## Early Exit Guard

If user said "remember X" with explicit content already in context:
1. Resolve memory path (see Phase 1 step 1)
2. Read existing memories to check for duplicates and pick the right layer
3. Skip to Phase 3 (Propose & Execute) with that content — no subagents needed

## Unified Workflow

### Phase 1: Orient (main session)

1. Resolve memory path: `Glob ~/.claude/projects/*<repo-dir-name>*/memory/MEMORY.md`
2. Read MEMORY.md + list topic files (`Glob memory/*.md` from resolved path)
3. Read both CLAUDE.md files (`~/.claude/CLAUDE.md` + `<repo>/CLAUDE.md`)
4. `git log --oneline -20`
5. Build context snapshot: summarize existing knowledge + list verification targets (file paths, functions, patterns named in memories)

### Phase 2: Gather (2 subagents in parallel)

Spawn both subagents in a single Agent tool message. Each is a general-purpose subagent with its mission embedded in the prompt. Pass the context snapshot from Phase 1 into both prompts.

**Subagent 1 — Memory Auditor**

Mission: For each memory that names a file path, function, version, or pattern, verify it still exists in the codebase. Cross-reference git log for contradictions. Report every stale, contradicted, or mergeable entry.

Input (embed in prompt): memory file contents, git log output, verification targets list.

Output format: list of candidates, each with:
- Category: STALE / CONTRADICT / MERGE / DATE_FIX
- Which memory entry (quote it)
- Evidence (what changed or is missing)
- Suggested action (EDIT / REMOVE with proposed replacement)

Quality rules: state principles not incidents, require codebase evidence for every finding, flag relative dates ("yesterday", "recently") for absolute conversion.

**Subagent 2 — Signal Discoverer**

Mission: Read recent sessions via `recent_chats.py --n 10 --project <project> --verbose`. Extract: user corrections, architectural decisions, recurring patterns, behavioral preferences. Generalize each to a principle. Ignore one-off debugging, tool output noise, and anything already in existing memories.

Input (embed in prompt): existing memory summaries (for dedup), project name, `CLAUDE_PLUGIN_ROOT` path for the script.

Output format: list of FILL_GAP candidates, each with:
- Principle (1-2 sentences, generalized)
- Evidence (which session, what the user said/did)
- Suggested layer (using placement decision)

Quality rules: generalize to principles not incidents, skip anything already captured in existing memories, skip generic programming advice.

### Phase 3: Synthesize & Propose (main session)

1. Receive both subagent reports
2. Deduplicate across reports and against existing memories
3. Rank by impact, limit to 3-7 candidates
4. For each candidate: determine target layer, target section, action (ADD / EDIT / REMOVE)
5. Read target files, check for duplicates
6. Present proposals:
   ```
   ### [ACTION] Learning: <summary>
   **Target:** <file> → <section>
   **Rationale:** <why this layer>
   ```diff
   + <new line>
   - <old line>
   ```
   ```
7. MEMORY.md line check — if over 170 lines, propose specific demotions to L3 or removals
8. Layer 0 gate — if targeting `~/.claude/CLAUDE.md`, warn: "This modifies global instructions loaded in every session across all projects. Confirm?"
9. AskUserQuestion: Approve all / Approve selectively / Reject

### Phase 4: Execute

Apply approved edits. Output summary table:

```
| Learning | Action | Target | Status |
|----------|--------|--------|--------|
```

Write consolidation marker: `Bash(date -u +%Y-%m-%dT%H:%M:%SZ)` → Write `.last-consolidation` in same directory as MEMORY.md.

## Content Quality Rules

Every candidate must pass: (1) agent would benefit from knowing this in future sessions, (2) condensed to minimum useful form, (3) placed at correct layer, (4) not already captured in target file, (5) stated as reusable principle not session-specific incident.

Pass: commands discovered through trial-and-error, non-obvious gotchas, architectural decisions with rationale, user behavioral corrections, configuration quirks, version milestones.

Fail: information readable from code, generic best practices, one-off bugs without pattern, verbose explanations, duplicates, temporary state, unverified speculation, incidents without generalizable principle.
