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
               b.files_modified, b.commits, s.git_branch, b.id as branch_db_id
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
        _session_id, uuid, started_at, ended_at, exchange_count, files_json, commits_json, git_branch, branch_db_id = session

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

    # Batch-load messages for all selected branches in a single query
    branch_ids = [s["branch_db_id"] for s in filtered]
    placeholders = ",".join("?" * len(branch_ids))
    cursor.execute(f"""
        SELECT bm.branch_id, m.role, m.content, m.timestamp, m.tool_summary
        FROM branch_messages bm
        JOIN messages m ON bm.message_id = m.id
        WHERE bm.branch_id IN ({placeholders})
          AND COALESCE(m.is_notification, 0) = 0
        ORDER BY bm.branch_id, m.timestamp ASC
    """, branch_ids)

    # Group messages by branch_id
    branch_messages = {}  # type: dict[int, list[dict]]
    for branch_id, role, content, timestamp, tool_summary in cursor.fetchall():
        branch_messages.setdefault(branch_id, []).append(
            {"role": role, "content": content, "timestamp": timestamp, "tool_summary": tool_summary}
        )

    for entry in filtered:
        entry["messages"] = branch_messages.get(entry["branch_db_id"], [])
        del entry["branch_db_id"]
        selected.append(entry)

    return selected


def _format_tool_summary(tool_summaries: list[str | None]) -> str:
    """Merge tool_summary JSON strings from multiple assistant messages into a compact line."""
    merged = {}  # type: dict[str, int]
    for raw in tool_summaries:
        if not raw:
            continue
        try:
            summary = json.loads(raw)
            for tool, count in summary.items():
                merged[tool] = merged.get(tool, 0) + count
        except (json.JSONDecodeError, AttributeError):
            continue
    if not merged:
        return ""
    parts = [f"{tool}({count})" for tool, count in merged.items()]
    return "Tools: " + ", ".join(parts)


def build_context(sessions: list[dict]) -> str:
    """Build markdown context from selected sessions."""
    if not sessions:
        return ""

    lines = []

    for i, session in enumerate(sessions):
        if i > 0:
            lines.append("\n---\n")

        # Session timeline with full date and optional branch
        start = format_time_full(session["started_at"])
        end = format_time_full(session["ended_at"])
        header = f"### Session: {start} -> {end}"
        branch = session.get("git_branch")
        if branch:
            header += f" (branch: {branch})"
        lines.append(header + "\n")

        # Topic line from first user message
        messages = session.get("messages", [])
        for m in messages:
            if m["role"] == "user" and m.get("content"):
                topic = m["content"].strip().replace("\n", " ")
                if len(topic) > 120:
                    topic = topic[:120] + "..."
                lines.append(f"**Topic:** {topic}\n")
                break

        # Files modified
        files = session.get("files_modified", [])
        if files:
            lines.append("### Files Modified")
            for f in files[-10:]:  # Last 10
                lines.append(f"- `{f}`")
            if len(files) > 10:
                lines.append(f"- ...and {len(files) - 10} more")
            lines.append("")

        # Git commits
        commits = session.get("commits", [])
        if commits:
            lines.append("### Git Commits")
            for c in commits:
                lines.append(f"- {c}")
            lines.append("")

        # Build exchange pairs from all messages
        if not messages:
            continue

        exchanges = []
        current_user = None
        current_asst = []
        current_tool_summaries = []  # type: list[str | None]

        for m in messages:
            if m["role"] == "user":
                if current_user is not None:
                    exchanges.append({
                        "user": current_user,
                        "asst": "\n\n".join(current_asst),
                        "ts": m["timestamp"],
                        "tools": list(current_tool_summaries),
                    })
                current_user = m["content"]
                current_asst = []
                current_tool_summaries = []
            elif m["role"] == "assistant" and current_user is not None:
                cleaned = re.sub(r'\[Tool: \w+\]', '', m["content"]).strip()
                if cleaned:
                    current_asst.append(cleaned)
                current_tool_summaries.append(m.get("tool_summary"))

        if current_user is not None:
            exchanges.append({
                "user": current_user,
                "asst": "\n\n".join(current_asst),
                "ts": None,
                "tools": list(current_tool_summaries),
            })

        if not exchanges:
            continue

        lines.append("### Where We Left Off\n")

        for ex in exchanges:
            t = format_time(ex.get("ts"))
            lines.append(f"**[{t}] User:**")
            lines.append(ex["user"])
            lines.append("")
            if ex["asst"]:
                lines.append(f"**[{t}] Assistant:**")
                lines.append(ex["asst"])
                tool_line = _format_tool_summary(ex.get("tools", []))
                if tool_line:
                    lines.append(tool_line)
                lines.append("")

    return "\n".join(lines)


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
