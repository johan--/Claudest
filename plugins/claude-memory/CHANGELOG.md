# Changelog

All notable changes to the claude-memory plugin are documented here.

## 0.7.2

Fix foreign key constraint crash on reimport, add versioned data migrations via `PRAGMA user_version`, and fix missing FK pragma after schema migration reconnect.

The FK delete order bug was introduced in v0.7.0 when `PRAGMA foreign_keys = ON` was enabled without updating the delete sequence in `import_session` — it deleted messages before their referencing `branch_messages` rows, causing `IntegrityError` on any reimport. The fix clears data in FK-safe order: branch_messages, then branches, then messages.

The teammate message backfill from v0.7.1 was unreachable for users upgrading from v0.7.0 because it was nested inside the `is_notification` column-existence check, which only fires when the column is first added. Data migrations now use `PRAGMA user_version` for version-gated execution independent of schema shape. The re-aggregation logic is extracted into `_reaggregate_notification_branches()` to avoid duplication between migration versions.

## 0.7.1

Filter teammate coordination messages and prompt_suggestion subagent noise from context injection.

Added `is_teammate_message()` detection for `<teammate-message>` XML-wrapped entries, reusing the same `is_notification` infrastructure as task notifications. Both `import_conversations.py` and `sync_current.py` now flag these at insert time, so all downstream filters (context injection, FTS aggregation, exchange counting) automatically exclude them. The `compute_branch_metadata()` function also skips teammate messages in exchange counting. A migration backfill flags existing teammate messages in the DB, and `import_project()` skips `prompt_suggestion` subagent files entirely during import.

## 0.7.0

Security hardening and performance improvements.

Five security enhancements: TOCTOU race prevention in `memory-sync.py` using `tempfile.mkstemp()` with 0o600 permissions, path traversal prevention in `sync_current.py` via UUID format validation and `resolve().relative_to()` boundary checks, FTS injection prevention through `sanitize_fts_term()` stripping operators and keywords, safe dynamic IN clause construction with auto-generated placeholders, and `PRAGMA foreign_keys = ON` enforcement to prevent orphaned records.

## 0.6.0

Add extract-learnings skill, rewrite READMEs, and add empty record prevention.

The extract-learnings skill is a pure prompt skill that bridges recall memory (past conversations) into archival memory (CLAUDE.md, MEMORY.md, topic files) using a 5-layer placement decision tree. Empty record prevention adds three guards to `import_session()`: sessions with zero messages are deleted, branches with empty aggregated content are removed, and sessions with zero surviving branches are cleaned up.

## 0.5.1

Cross-platform support with FTS fallback.

All hooks converted from bash to Python for Windows compatibility. Added `from __future__ import annotations` across all files for Python 3.7+ support. Removed `RETURNING` SQL clauses (not available in older SQLite) in favor of `cursor.lastrowid`. Removed PyYAML dependency — settings are now hardcoded defaults only. FTS support cascades from FTS5 to FTS4 to LIKE fallback, detected via `PRAGMA compile_options`.

## 0.5.0

Filter task notification messages from context and search.

Added `is_task_notification()` to detect `<task-notification>` entries. These are flagged with `is_notification = 1` at import time and excluded from context injection queries, FTS branch aggregation, and exchange counting. Added comprehensive test suite with pytest covering content extraction, parsing, branch detection, and the import pipeline.

## 0.4.0

Branch-level FTS index for session search.

Added `aggregate_branch_content()` in `parsing.py` that concatenates all non-notification messages for a branch in timestamp order. Branch content is stored in `branches.aggregated_content` and indexed via `branches_fts` virtual table. Search queries now hit `branches_fts` directly with level-appropriate SQL (BM25 ranking for FTS5, recency for FTS4).

## 0.3.1

Remove message truncation from context injection.

Full conversation dump — all exchanges rendered in order, no truncation, no tiering. The old approach (Session Goal / Other Requests / Where We Left Off with last-3 and 2000-char truncation) was removed because tool markers are now cleaned at import time, making stored assistant messages pure prose.

## 0.3.0

Tool usage tracking and shared utility refactoring.

`extract_text_content()` now returns a 4-tuple including `tool_summary_json`. Tool markers are not materialized into stored text; instead tool counts are stored as compact JSON in `messages.tool_summary`. Shared code split into modular `memory_lib` package: `db.py`, `content.py`, `parsing.py`, `formatting.py`.

## 0.2.0

v3 schema with branch-aware conversation storage.

Messages stored once per session (deduped), branches tracked via many-to-many `branch_messages` table. Branch detection uses UUID parent chain analysis to find conversation rewinds. Added `sessions.cwd`, `sessions.git_branch`, `branches.files_modified`, `branches.commits` metadata fields.

## 0.1.0

Initial release with conversation search and sync.

SessionStart hooks create the DB directory and inject previous session context. Stop hook syncs the current session to SQLite in the background. Basic full-text search via FTS5 with message-level indexing.
