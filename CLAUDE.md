# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudest is a curated Claude Code plugin marketplace containing two plugins: **claude-memory** (conversation memory with FTS5 search and context injection) and **claude-utilities** (web-to-markdown via ezycopy). There is no build system, test runner, or package manager — scripts are Python 3 stdlib-only and tested through real usage.

## Development Commands

```bash
# Re-import all conversations into the memory DB
python3 plugins/claude-memory/hooks/import_conversations.py

# Import with stats output
python3 plugins/claude-memory/hooks/import_conversations.py --stats

# Test context injection manually
echo '{"source":"startup","session_id":"test","cwd":"/some/path"}' | python3 plugins/claude-memory/hooks/memory-context.py

# Test session sync manually
echo '{"session_id":"<uuid>"}' | python3 plugins/claude-memory/hooks/sync_current.py
```

No `--force` flag exists for import — delete `~/.claude-memory/conversations.db` and re-run to reimport from scratch.

## Architecture

### Plugin Structure

Each plugin follows the Claude Code plugin convention: `.claude-plugin/plugin.json` for metadata, `hooks/` for lifecycle hooks, `commands/` for slash commands, and `skills/` for auto-triggered capabilities.

### claude-memory Hook Lifecycle

On **SessionStart**, two hooks fire in order: `memory-setup.sh` creates the `~/.claude-memory/` directory and kicks off a background import if the DB doesn't exist, then `memory-context.py` (on `startup|clear` events only) queries recent sessions and injects them as additional context via `hookSpecificOutput`. On **Stop**, `memory-sync.sh` spawns `sync_current.py` in the background (`nohup ... & disown`) to incrementally sync the current session to the DB without blocking shutdown.

### Database (v3 Schema)

SQLite at `~/.claude-memory/conversations.db`. The key design: messages are stored once per session (deduped), and branches (from conversation rewinds) are tracked via a many-to-many `branch_messages` table. Two FTS5 indexes provide full-text search: `messages_fts` indexes individual messages, while `branches_fts` indexes aggregated branch content (all messages concatenated per branch) for BM25-ranked session search. Schema is defined in `memory_lib/db.py:SCHEMA` and auto-migrated on connection — if the schema version is outdated, the DB is deleted and recreated.

Tables: `projects`, `sessions`, `branches`, `messages`, `branch_messages`, `import_log`, `messages_fts` (virtual), `branches_fts` (virtual).

### Shared Code

`plugins/claude-memory/skills/past-conversations/scripts/memory_lib/` is the shared utility package used by all hooks and skill scripts. It is split into four focused modules: `db.py` (database connection, schema, settings, logging), `content.py` (message content extraction and tool detection), `parsing.py` (JSONL parsing, branch detection via UUID parent chain analysis, metadata extraction), and `formatting.py` (session formatting, time/path utilities). The `extract_text_content()` function in `content.py` returns a 4-tuple `(text, has_tool_use, has_thinking, tool_summary_json)` — tool markers are never materialized into stored text; instead tool counts are stored as compact JSON in `messages.tool_summary`.

### Session Selection Algorithm

`memory-context.py:select_sessions` iterates recent sessions (excluding current session and subagents), skips those with `exchange_count <= 1`. For 2-exchange sessions it appends and keeps looking (up to `max_context_sessions`). For sessions with >2 exchanges it appends and stops. This means multiple sessions are only injected when the most recent ones are very short.

## Conventions

Commit messages use conventional commits: `feat(memory):`, `fix(memory):`, `chore(memory):`, `docs:`, `refactor(memory):`. Version is tracked in two places that must stay in sync: each plugin's `.claude-plugin/plugin.json` and the root `.claude-plugin/marketplace.json`. Always bump version before pushing changes.

Settings live in `~/.claude-memory/settings.local.md` (YAML frontmatter), with defaults defined in `memory_lib/db.py:DEFAULT_SETTINGS`.
