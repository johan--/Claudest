#!/usr/bin/env python3
"""
Search conversations using FTS5 full-text search.

Returns markdown by default (token-efficient), JSON with --format json.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Local imports
from memory_lib.db import DEFAULT_DB_PATH
from memory_lib.formatting import format_markdown_session, format_json_sessions


def search_sessions(
    conn: sqlite3.Connection,
    query: str,
    max_results: int = 5,
    projects: list[str] | None = None,
    verbose: bool = False
) -> list[dict]:
    """Search for sessions using branch-level FTS with BM25 ranking."""
    cursor = conn.cursor()

    terms = query.split()
    if not terms:
        return []

    fts_query = " OR ".join(f'"{term}"' for term in terms)

    # Single query: branch-level FTS with BM25 ranking
    sql = """
        SELECT s.id, s.uuid, b.started_at, b.ended_at, b.files_modified,
               b.commits, s.git_branch, p.name as project, b.id as branch_db_id
        FROM branches_fts
        JOIN branches b ON branches_fts.rowid = b.id
        JOIN sessions s ON b.session_id = s.id
        JOIN projects p ON s.project_id = p.id
        WHERE b.is_active = 1
          AND branches_fts MATCH ?
    """
    params: list = [fts_query]

    if projects:
        placeholders = ",".join("?" * len(projects))
        sql += f" AND p.name IN ({placeholders})"
        params.extend(projects)

    sql += " ORDER BY bm25(branches_fts) LIMIT ?"
    params.append(max_results)

    cursor.execute(sql, params)
    sessions = cursor.fetchall()

    results = []

    for session in sessions:
        _session_id, uuid, started_at, ended_at, files_json, commits_json, git_branch, project, branch_db_id = session

        # Get messages for active branch via branch_messages
        cursor.execute("""
            SELECT m.role, m.content, m.timestamp
            FROM branch_messages bm
            JOIN messages m ON bm.message_id = m.id
            WHERE bm.branch_id = ?
            ORDER BY m.timestamp ASC
        """, (branch_db_id,))

        messages = [{"role": r, "content": c, "timestamp": t} for r, c, t in cursor.fetchall()]

        session_data = {
            "uuid": uuid,
            "project": project,
            "started_at": started_at,
            "ended_at": ended_at,
            "git_branch": git_branch,
            "messages": messages
        }

        if verbose:
            session_data["files_modified"] = json.loads(files_json) if files_json else []
            session_data["commits"] = json.loads(commits_json) if commits_json else []

        results.append(session_data)

    return results


def format_markdown(sessions: list[dict], query: str, verbose: bool = False) -> str:
    """Format sessions as markdown."""
    if not sessions:
        return f"No sessions found for query: {query}"

    lines = [f"# Search Results: \"{query}\" ({len(sessions)} sessions)\n"]
    for session in sessions:
        lines.append(format_markdown_session(session, verbose=verbose))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search conversation sessions")
    parser.add_argument("--query", "-q", type=str, required=True, help="Search keywords")
    parser.add_argument("--max-results", type=int, default=5, help="Max sessions (1-10, default: 5)")
    parser.add_argument("--project", type=str, help="Filter by project name(s), comma-separated")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Include files_modified and commits")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Database path")

    args = parser.parse_args()
    max_results = max(1, min(10, args.max_results))
    projects = [p.strip() for p in args.project.split(",")] if args.project else None

    if not args.db.exists():
        if args.format == "json":
            print(json.dumps({"error": "Database not found", "sessions": [], "query": args.query}))
        else:
            print("Error: Database not found. Run memory setup first.")
        sys.exit(1)

    try:
        conn = sqlite3.connect(args.db)
        sessions = search_sessions(conn, query=args.query, max_results=max_results,
                                   projects=projects, verbose=args.verbose)
        conn.close()

        if args.format == "json":
            print(format_json_sessions(sessions, {"query": args.query})  )
        else:
            print(format_markdown(sessions, args.query, verbose=args.verbose))

    except Exception as e:
        if args.format == "json":
            print(json.dumps({"error": str(e), "sessions": [], "query": args.query}))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
