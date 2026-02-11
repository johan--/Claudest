#!/usr/bin/env python3
"""
Database connection, schema management, settings, and logging.
"""

import logging
import sqlite3
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Default paths
DEFAULT_DB_PATH = Path.home() / ".claude-memory" / "conversations.db"
DEFAULT_PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_SETTINGS_PATH = Path.home() / ".claude-memory" / "settings.local.md"
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
SCHEMA = """
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

-- FTS5 full-text search (auto-synced via triggers)
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

-- Branch-level FTS5 (aggregated content per branch, ranked by BM25)
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

-- Import tracking
CREATE TABLE IF NOT EXISTS import_log (
  id INTEGER PRIMARY KEY,
  file_path TEXT UNIQUE NOT NULL,
  file_hash TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  messages_imported INTEGER DEFAULT 0
);

-- Views
CREATE VIEW IF NOT EXISTS search_results AS
SELECT m.id, m.timestamp, m.role, m.content, s.uuid as session_uuid, p.name as project_name, p.path as project_path
FROM messages m JOIN sessions s ON m.session_id = s.id JOIN projects p ON s.project_id = p.id;

CREATE VIEW IF NOT EXISTS recent_conversations AS
SELECT s.uuid as session_uuid, b.leaf_uuid as branch_id, b.is_active as is_active_branch,
       p.name as project, b.started_at, b.ended_at,
       b.exchange_count, b.files_modified, b.commits, s.git_branch
FROM sessions s
JOIN branches b ON b.session_id = s.id
JOIN projects p ON s.project_id = p.id
ORDER BY b.ended_at DESC;
"""


def migrate_db(conn: sqlite3.Connection) -> bool:
    """
    Migrate database to v3 schema (messages-once + branch index).
    Detects old schema by checking if 'branches' table exists.
    If not, deletes the DB file so memory-setup.sh triggers a fresh import.
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
    new_conn.executescript(SCHEMA)
    new_conn.commit()

    # We can't return the new connection through the old reference,
    # so we signal that migration happened and caller should reconnect
    new_conn.close()
    return True


def load_settings(settings_path: Optional[Path] = None) -> dict:
    """
    Load settings from YAML frontmatter in settings file.
    Returns default settings if file doesn't exist or parsing fails.
    """
    path = settings_path or DEFAULT_SETTINGS_PATH
    settings = DEFAULT_SETTINGS.copy()

    if not path.exists():
        return settings

    if not HAS_YAML:
        return settings

    try:
        content = path.read_text()
        # Parse YAML frontmatter (between --- markers)
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])  # type: ignore[possibly-undefined]
                if isinstance(frontmatter, dict):
                    settings.update(frontmatter)
    except Exception:
        pass

    return settings


def get_db_path(settings: Optional[dict] = None) -> Path:
    """Get database path from settings or default."""
    if settings and "db_path" in settings:
        return Path(settings["db_path"]).expanduser()
    return DEFAULT_DB_PATH


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add any missing columns to existing tables (idempotent)."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(messages)")
    existing = {row[1] for row in cursor.fetchall()}
    if "tool_summary" not in existing:
        cursor.execute("ALTER TABLE messages ADD COLUMN tool_summary TEXT")
        conn.commit()
    if "is_notification" not in existing:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_notification INTEGER DEFAULT 0")
        # Backfill existing notification messages
        cursor.execute("""
            UPDATE messages SET is_notification = 1
            WHERE role = 'user' AND content LIKE '<task-notification>%'
        """)
        # Re-aggregate branches that contained notifications (fix FTS + exchange_count)
        cursor.execute("""
            SELECT DISTINCT bm.branch_id
            FROM branch_messages bm
            JOIN messages m ON bm.message_id = m.id
            WHERE m.is_notification = 1
        """)
        affected_branches = [row[0] for row in cursor.fetchall()]
        for bid in affected_branches:
            # Re-aggregate content excluding notifications
            cursor.execute("""
                SELECT m.content FROM branch_messages bm
                JOIN messages m ON bm.message_id = m.id
                WHERE bm.branch_id = ? AND COALESCE(m.is_notification, 0) = 0
                ORDER BY m.timestamp ASC
            """, (bid,))
            agg = "\n".join(row[0] for row in cursor.fetchall())
            cursor.execute("UPDATE branches SET aggregated_content = ? WHERE id = ?", (agg, bid))
            # Recalculate exchange_count (human user messages only)
            cursor.execute("""
                SELECT COUNT(*) FROM branch_messages bm
                JOIN messages m ON bm.message_id = m.id
                WHERE bm.branch_id = ? AND m.role = 'user' AND COALESCE(m.is_notification, 0) = 0
            """, (bid,))
            human_user_count = cursor.fetchone()[0]
            cursor.execute("UPDATE branches SET exchange_count = ? WHERE id = ?",
                           (human_user_count, bid))
        conn.commit()


def get_db_connection(settings: Optional[dict] = None) -> sqlite3.Connection:
    """
    Get database connection, initializing schema and running migrations if needed.
    Uses settings-based path if provided.
    """
    db_path = get_db_path(settings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    # Check if migration needed (old schema -> v3)
    migrated = migrate_db(conn)
    if migrated:
        # Connection was closed during migration, reconnect
        conn = sqlite3.connect(db_path)
    else:
        # Apply schema (handles fresh databases, idempotent)
        conn.executescript(SCHEMA)
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
