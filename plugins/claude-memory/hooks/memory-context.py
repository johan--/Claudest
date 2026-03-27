#!/usr/bin/env python3
"""
Load previous session context from memory database for SessionStart hook.

Selection Algorithm:
1. Get recent sessions for current project (excluding current session)
2. Skip sessions with exchange_count <= 1 (noise)
3. Load sessions with exchange_count == 2, keep looking (up to MAX_SESSIONS)
4. Stop at first session with exchange_count > 2 (sufficient context)

Output: JSON with hookSpecificOutput for context injection
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

# Add path to shared utils
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "skills" / "recall-conversations" / "scripts"))

from memory_lib.db import get_db_path, load_settings, setup_logging
from memory_lib.formatting import format_time, format_time_full, get_project_key
from memory_lib.summarizer import _build_exchange_pairs, _truncate_mid


def select_sessions(conn: sqlite3.Connection, project_key: str, current_session_id: str, max_sessions: int) -> list[dict]:
    """
    Select sessions for context using the exchange-count algorithm.
    Returns list of session dicts with messages.
    """
    cursor = conn.cursor()

    # Get project ID
    cursor.execute("SELECT id FROM projects WHERE key = ?", (project_key,))
    row = cursor.fetchone()
    if not row:
        return []
    project_id = row[0]

    # Get recent active branches (by last activity), excluding current and subagents
    cursor.execute("""
        SELECT s.id, s.uuid, b.started_at, b.ended_at, b.exchange_count,
               b.files_modified, b.commits, s.git_branch, b.id as branch_db_id,
               b.context_summary
        FROM sessions s
        JOIN branches b ON b.session_id = s.id AND b.is_active = 1
        WHERE s.project_id = ?
          AND s.uuid != ?
          AND s.parent_session_id IS NULL
        ORDER BY b.ended_at DESC
        LIMIT 20
    """, (project_id, current_session_id))

    candidates = cursor.fetchall()
    selected = []

    # First pass: filter candidates using the exchange-count algorithm
    filtered = []
    for session in candidates:
        _session_id, uuid, started_at, ended_at, exchange_count, files_json, commits_json, git_branch, branch_db_id, context_summary = session

        if exchange_count <= 1:
            continue

        entry = {
            "uuid": uuid,
            "started_at": started_at,
            "ended_at": ended_at,
            "exchange_count": exchange_count,
            "files_modified": json.loads(files_json) if files_json else [],
            "commits": json.loads(commits_json) if commits_json else [],
            "git_branch": git_branch,
            "branch_db_id": branch_db_id,
            "context_summary": context_summary,
        }

        if exchange_count == 2:
            filtered.append(entry)
            if len(filtered) >= max_sessions:
                break
            continue

        if exchange_count > 2:
            filtered.append(entry)
            break

    if not filtered:
        return selected

    # Split into cached (has context_summary) and uncached
    uncached_ids = [s["branch_db_id"] for s in filtered if not s.get("context_summary")]

    # Only batch-load messages for uncached branches
    branch_messages = {}  # type: dict[int, list[dict]]
    if uncached_ids:
        placeholders = ",".join("?" * len(uncached_ids))
        cursor.execute(f"""
            SELECT bm.branch_id, m.role, m.content, m.timestamp
            FROM branch_messages bm
            JOIN messages m ON bm.message_id = m.id
            WHERE bm.branch_id IN ({placeholders})
              AND COALESCE(m.is_notification, 0) = 0
            ORDER BY bm.branch_id, m.timestamp ASC
        """, uncached_ids)

        for branch_id, role, content, timestamp in cursor.fetchall():
            branch_messages.setdefault(branch_id, []).append(
                {"role": role, "content": content, "timestamp": timestamp}
            )

    for entry in filtered:
        if not entry.get("context_summary"):
            entry["messages"] = branch_messages.get(entry["branch_db_id"], [])
        del entry["branch_db_id"]
        selected.append(entry)

    return selected


def _build_fallback_context(session: dict) -> str:
    """
    Fallback for sessions without cached context_summary.
    Renders truncated last-3 exchanges in the same format as render_context_summary.
    """
    lines = []

    # Session header
    start = format_time_full(session["started_at"])
    end = format_time_full(session["ended_at"])
    header = f"### Session: {start} -> {end}"
    branch = session.get("git_branch")
    if branch:
        header += f" (branch: {branch})"
    lines.append(header + "\n")

    # Files modified (compact)
    files = session.get("files_modified", [])
    if files:
        file_strs = [f"`{f}`" for f in files[:6]]
        line = "Modified: " + ", ".join(file_strs)
        if len(files) > 6:
            line += f" +{len(files) - 6} more"
        lines.append(line)

    # Commits
    commits = session.get("commits", [])
    if commits:
        lines.append("Commits: " + "; ".join(commits[:3]))

    lines.append("")

    # Build exchanges from messages
    messages = session.get("messages", [])
    if not messages:
        return "\n".join(lines)

    exchanges = _build_exchange_pairs(messages)
    if not exchanges:
        return "\n".join(lines)

    exchange_count = session.get("exchange_count", len(exchanges))

    if len(exchanges) <= 3:
        lines.append("### Conversation\n")
        for ex in exchanges:
            t = format_time(ex.get("timestamp"))
            lines.append(f"**[{t}] User:**")
            lines.append(ex["user"])
            lines.append("")
            if ex["assistant"]:
                lines.append(f"**[{t}] Assistant:**")
                lines.append(_truncate_mid(ex["assistant"]))
                lines.append("")
    else:
        # First exchange
        first = exchanges[0]
        lines.append("### First Exchange\n")
        t = format_time(first.get("timestamp"))
        lines.append(f"**[{t}] User:**")
        lines.append(first["user"])
        lines.append("")
        if first["assistant"]:
            lines.append(f"**[{t}] Assistant:**")
            lines.append(_truncate_mid(first["assistant"]))
            lines.append("")

        # Gap
        gap = len(exchanges) - 4
        if gap > 0:
            lines.append(f"[... {gap} exchanges ...]\n")

        # Last 3 exchanges
        lines.append("### Where We Left Off\n")
        for ex in exchanges[-3:]:
            t = format_time(ex.get("timestamp"))
            lines.append(f"**[{t}] User:**")
            lines.append(ex["user"])
            lines.append("")
            if ex["assistant"]:
                lines.append(f"**[{t}] Assistant:**")
                lines.append(_truncate_mid(ex["assistant"]))
                lines.append("")

    # Recall priming footer
    lines.append(
        f"[{exchange_count} total exchanges — proactively use /recall-conversations "
        "to retrieve relevant context from past conversations when the user references "
        "prior work, asks about decisions made earlier, or when you sense useful context "
        "from previous sessions would improve your response.]"
    )

    return "\n".join(lines)


def build_context(sessions: list[dict]) -> str:
    """Build markdown context from selected sessions.

    Uses cached context_summary when available, falls back to
    truncated last-3 exchanges for uncached branches.
    """
    if not sessions:
        return ""

    parts = []
    for session in sessions:
        cached = session.get("context_summary")
        if cached:
            parts.append(cached)
        else:
            parts.append(_build_fallback_context(session))

    return "\n\n---\n\n".join(parts)


def main():
    # Load settings
    settings = load_settings()
    logger = setup_logging(settings)

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    cwd = hook_input.get("cwd")
    session_id = hook_input.get("session_id")
    source = hook_input.get("source", "startup")

    # Only inject on fresh sessions
    if source not in ("startup", "clear"):
        print(json.dumps({}))
        return

    # Check if auto-inject is disabled
    if not settings.get("auto_inject_context", True):
        logger.info("Context injection disabled by settings")
        print(json.dumps({}))
        return

    if not cwd or not session_id:
        print(json.dumps({}))
        return

    # Check if database exists
    db_path = get_db_path(settings)
    if not db_path.exists():
        print(json.dumps({}))
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        project_key = get_project_key(cwd)
        max_sessions = settings.get("max_context_sessions", 2)
        sessions = select_sessions(conn, project_key, session_id, max_sessions)
        conn.close()

        if not sessions:
            print(json.dumps({}))
            return

        context = build_context(sessions)
        if not context:
            print(json.dumps({}))
            return

        logger.info(f"Injecting context from {len(sessions)} session(s) for project {project_key}")

        # Wrap in section header
        full_context = f"## Previous Session Context\n\n{context}"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": full_context
            }
        }
        print(json.dumps(output))

    except Exception as e:
        logger.error(f"Context injection error: {e}")
        # Don't block session start on errors
        print(json.dumps({}))
        sys.exit(0)


if __name__ == "__main__":
    main()
