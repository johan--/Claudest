#!/usr/bin/env python3
"""
Database connection, schema management, settings, and logging.
"""

from __future__ import annotations

import logging
import sqlite3
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Default paths
DEFAULT_DB_PATH = Path.home() / ".claude-memory" / "conversations.db"
DEFAULT_PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_LOG_PATH = Path.home() / ".claude-memory" / "memory.log"

# Default settings
DEFAULT_SETTINGS = {
    "db_path": str(DEFAULT_DB_PATH),
    "auto_inject_context": True,
    "max_context_sessions": 2,
    "exclude_projects": [],
    "logging_enabled": False,
    "sync_on_stop": True,
}

# Database schema — v3: messages stored once, branches as separate index
# Split into core (tables/indexes) and FTS variants for compatibility
SCHEMA_CORE = """
-- Projects table (derived from directory structure)
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  key TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_projects_key ON projects(key);

-- Sessions table (ONE row per session UUID)
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY,
  uuid TEXT UNIQUE NOT NULL,
  project_id INTEGER REFERENCES projects(id),
  parent_session_id INTEGER REFERENCES sessions(id),
  git_branch TEXT,
  cwd TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);

-- Branches table (one row per branch per session)
CREATE TABLE IF NOT EXISTS branches (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  leaf_uuid TEXT NOT NULL,
  fork_point_uuid TEXT,
  is_active INTEGER DEFAULT 1,
  started_at DATETIME,
  ended_at DATETIME,
  exchange_count INTEGER DEFAULT 0,
  files_modified TEXT,
  commits TEXT,
  aggregated_content TEXT,
  UNIQUE(session_id, leaf_uuid)
);
CREATE INDEX IF NOT EXISTS idx_branches_session ON branches(session_id);
CREATE INDEX IF NOT EXISTS idx_branches_active ON branches(is_active);

-- Messages table (ALL messages stored ONCE per session)
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  uuid TEXT,
  parent_uuid TEXT,
  timestamp DATETIME,
  role TEXT CHECK(role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_summary TEXT,
  has_tool_use INTEGER DEFAULT 0,
  has_thinking INTEGER DEFAULT 0,
  is_notification INTEGER DEFAULT 0,
  UNIQUE(session_id, uuid)
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_session_uuid ON messages(session_id, uuid);

-- Branch-messages mapping (many-to-many)
CREATE TABLE IF NOT EXISTS branch_messages (
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  message_id INTEGER NOT NULL REFERENCES messages(id),
  PRIMARY KEY (branch_id, message_id)
);
CREATE INDEX IF NOT EXISTS idx_branch_messages_message ON branch_messages(message_id);

-- Import tracking
CREATE TABLE IF NOT EXISTS import_log (
  id INTEGER PRIMARY KEY,
  file_path TEXT UNIQUE NOT NULL,
  file_hash TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  messages_imported INTEGER DEFAULT 0
);

"""

# FTS5 schema (best: porter stemming + unicode61, BM25 ranking)
SCHEMA_FTS5 = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  content,
  content=messages,
  content_rowid=id,
  tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
  INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS branches_fts USING fts5(
  aggregated_content,
  content=branches,
  content_rowid=id,
  tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS branches_ai AFTER INSERT ON branches BEGIN
  INSERT INTO branches_fts(rowid, aggregated_content) VALUES (new.id, new.aggregated_content);
END;
CREATE TRIGGER IF NOT EXISTS branches_ad AFTER DELETE ON branches BEGIN
  INSERT INTO branches_fts(branches_fts, rowid, aggregated_content) VALUES('delete', old.id, old.aggregated_content);
END;
CREATE TRIGGER IF NOT EXISTS branches_au AFTER UPDATE ON branches BEGIN
  INSERT INTO branches_fts(branches_fts, rowid, aggregated_content) VALUES('delete', old.id, old.aggregated_content);
  INSERT INTO branches_fts(rowid, aggregated_content) VALUES (new.id, new.aggregated_content);
END;
"""

# FTS4 schema (fallback: porter stemming, no BM25 but supports MATCH + snippet)
SCHEMA_FTS4 = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts4(
  content,
  content=messages,
  tokenize=porter
);

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
  INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS branches_fts USING fts4(
  aggregated_content,
  content=branches,
  tokenize=porter
);

CREATE TRIGGER IF NOT EXISTS branches_ai AFTER INSERT ON branches BEGIN
  INSERT INTO branches_fts(rowid, aggregated_content) VALUES (new.id, new.aggregated_content);
END;
CREATE TRIGGER IF NOT EXISTS branches_ad AFTER DELETE ON branches BEGIN
  INSERT INTO branches_fts(branches_fts, rowid, aggregated_content) VALUES('delete', old.id, old.aggregated_content);
END;
CREATE TRIGGER IF NOT EXISTS branches_au AFTER UPDATE ON branches BEGIN
  INSERT INTO branches_fts(branches_fts, rowid, aggregated_content) VALUES('delete', old.id, old.aggregated_content);
  INSERT INTO branches_fts(rowid, aggregated_content) VALUES (new.id, new.aggregated_content);
END;
"""

# Combined schema (core + FTS5) for test fixtures and simple single-shot setup
SCHEMA = SCHEMA_CORE + SCHEMA_FTS5


def detect_fts_support(conn: sqlite3.Connection) -> str | None:
    """Detect the best available FTS extension."""
    try:
        opts = {row[0] for row in conn.execute("PRAGMA compile_options").fetchall()}
    except Exception:
        return None
    if "ENABLE_FTS5" in opts:
        return "fts5"
    if "ENABLE_FTS4" in opts or "ENABLE_FTS3" in opts:
        return "fts4"
    return None


def migrate_db(conn: sqlite3.Connection) -> bool:
    """
    Migrate database to v3 schema (messages-once + branch index).
    Detects old schema by checking if 'branches' table exists.
    If not, deletes the DB file so a fresh import is triggered.
    Returns True if migration was performed (DB was deleted and recreated).
    """
    cursor = conn.cursor()

    # Check if branches table exists (v3 indicator)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branches'")
    if cursor.fetchone():
        return False  # Already on v3

    # Check if sessions table exists at all (could be a fresh DB)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    if not cursor.fetchone():
        return False  # Fresh DB, no migration needed

    # Old schema detected — nuke and recreate
    db_path = None
    # Get the database file path from connection
    cursor.execute("PRAGMA database_list")
    for row in cursor.fetchall():
        if row[1] == "main" and row[2]:
            db_path = Path(row[2])
            break

    conn.close()

    if db_path and db_path.exists():
        db_path.unlink()

    # Reconnect and create fresh schema
    new_conn = sqlite3.connect(str(db_path) if db_path else ":memory:")
    new_conn.execute("PRAGMA journal_mode = WAL")
    new_conn.execute("PRAGMA busy_timeout = 5000")
    fts = detect_fts_support(new_conn)
    new_conn.executescript(SCHEMA_CORE)
    if fts == "fts5":
        new_conn.executescript(SCHEMA_FTS5)
    elif fts == "fts4":
        new_conn.executescript(SCHEMA_FTS4)
    new_conn.commit()

    # We can't return the new connection through the old reference,
    # so we signal that migration happened and caller should reconnect
    new_conn.close()
    return True


def load_settings() -> dict:
    """
    Return default settings.
    Previously loaded from YAML frontmatter, but PyYAML is not stdlib
    so settings were silently ignored for most users.
    """
    return DEFAULT_SETTINGS.copy()


def get_db_path(settings: Optional[dict] = None) -> Path:
    """Get database path from settings or default."""
    if settings and "db_path" in settings:
        return Path(settings["db_path"]).expanduser()
    return DEFAULT_DB_PATH


def _reaggregate_notification_branches(cursor: sqlite3.Cursor) -> None:
    """Re-aggregate branches that contain notification messages.

    Updates aggregated_content and exchange_count to exclude notifications.
    Called after backfilling is_notification on existing messages.
    """
    cursor.execute("""
        SELECT DISTINCT bm.branch_id
        FROM branch_messages bm
        JOIN messages m ON bm.message_id = m.id
        WHERE m.is_notification = 1
    """)
    affected_branches = [row[0] for row in cursor.fetchall()]
    for bid in affected_branches:
        cursor.execute("""
            SELECT m.content FROM branch_messages bm
            JOIN messages m ON bm.message_id = m.id
            WHERE bm.branch_id = ? AND COALESCE(m.is_notification, 0) = 0
            ORDER BY m.timestamp ASC
        """, (bid,))
        agg = "\n".join(row[0] for row in cursor.fetchall())
        cursor.execute("UPDATE branches SET aggregated_content = ? WHERE id = ?", (agg, bid))
        cursor.execute("""
            SELECT COUNT(*) FROM branch_messages bm
            JOIN messages m ON bm.message_id = m.id
            WHERE bm.branch_id = ? AND m.role = 'user' AND COALESCE(m.is_notification, 0) = 0
        """, (bid,))
        human_user_count = cursor.fetchone()[0]
        cursor.execute("UPDATE branches SET exchange_count = ? WHERE id = ?",
                       (human_user_count, bid))


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add missing columns (DDL, idempotent) and run versioned data migrations (DML)."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(messages)")
    existing = {row[1] for row in cursor.fetchall()}

    # --- DDL migrations (column-existence gated, idempotent) ---
    if "tool_summary" not in existing:
        cursor.execute("ALTER TABLE messages ADD COLUMN tool_summary TEXT")
        conn.commit()
    if "is_notification" not in existing:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_notification INTEGER DEFAULT 0")
        conn.commit()

    # --- DML migrations (version-gated via PRAGMA user_version, run once) ---
    version = conn.execute("PRAGMA user_version").fetchone()[0]

    if version < 1:
        # v0.5.0: Backfill task-notification messages
        cursor.execute("""
            UPDATE messages SET is_notification = 1
            WHERE role = 'user' AND content LIKE '<task-notification>%' AND is_notification = 0
        """)
        _reaggregate_notification_branches(cursor)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()

    if version < 2:
        # v0.7.1: Backfill teammate messages as notifications
        cursor.execute("""
            UPDATE messages SET is_notification = 1
            WHERE role = 'user' AND content LIKE '<teammate-message%' AND is_notification = 0
        """)
        _reaggregate_notification_branches(cursor)
        conn.execute("PRAGMA user_version = 2")
        conn.commit()


def get_db_connection(settings: Optional[dict] = None) -> sqlite3.Connection:
    """
    Get database connection, initializing schema and running migrations if needed.
    Uses settings-based path if provided.
    Sets WAL mode and busy_timeout for concurrent access safety.
    """
    db_path = get_db_path(settings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    # WAL mode: readers never block writers, writers never block readers
    conn.execute("PRAGMA journal_mode = WAL")
    # busy_timeout: wait up to 5s on writer-writer collisions instead of failing
    conn.execute("PRAGMA busy_timeout = 5000")
    # Enforce foreign key constraints to prevent orphaned data
    conn.execute("PRAGMA foreign_keys = ON")

    # Check if migration needed (old schema -> v3)
    migrated = migrate_db(conn)
    if migrated:
        # Connection was closed during migration, reconnect
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA foreign_keys = ON")

    if not migrated:
        # Apply schema (handles fresh databases, idempotent)
        fts = detect_fts_support(conn)
        conn.executescript(SCHEMA_CORE)
        if fts == "fts5":
            conn.executescript(SCHEMA_FTS5)
        elif fts == "fts4":
            conn.executescript(SCHEMA_FTS4)
        conn.commit()

    # Add any missing columns (e.g. tool_summary)
    _migrate_columns(conn)

    return conn



def setup_logging(settings: Optional[dict] = None) -> logging.Logger:
    """
    Set up logging with rotation.
    Returns a null logger if logging is disabled.
    """
    logger = logging.getLogger("claude-memory")
    logger.handlers = []  # Clear existing handlers

    if not settings or not settings.get("logging_enabled", False):
        logger.addHandler(logging.NullHandler())
        return logger

    log_path = DEFAULT_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,  # 1MB
        backupCount=2
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger
