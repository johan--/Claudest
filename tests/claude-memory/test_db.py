"""Tests for memory_lib.db — schema creation, migration, settings."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from memory_lib.db import (
    DEFAULT_SETTINGS,
    SCHEMA,
    _migrate_columns,
    load_settings,
    migrate_db,
)


class TestSchemaCreation:
    def test_all_tables_exist(self, memory_db):
        cursor = memory_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}
        expected = {"projects", "sessions", "branches", "messages", "branch_messages", "import_log"}
        assert expected.issubset(tables)

    def test_fts_tables_exist(self, memory_db):
        cursor = memory_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts%'")
        fts_tables = {row[0] for row in cursor.fetchall()}
        assert "messages_fts" in fts_tables
        assert "branches_fts" in fts_tables

    def test_schema_idempotent(self, memory_db):
        """Applying schema twice should not raise."""
        memory_db.executescript(SCHEMA)
        memory_db.commit()

    def test_insert_and_query(self, memory_db):
        """Basic insert/query roundtrip."""
        cursor = memory_db.cursor()
        cursor.execute("INSERT INTO projects (path, key, name) VALUES (?, ?, ?)",
                       ("/home/user/project", "-home-user-project", "project"))
        cursor.execute("INSERT INTO sessions (uuid, project_id) VALUES (?, ?)",
                       ("sess-1", cursor.lastrowid))
        memory_db.commit()
        cursor.execute("SELECT uuid FROM sessions")
        assert cursor.fetchone()[0] == "sess-1"


def _pre_migration_db(include_tool_summary=False):
    """Create in-memory DB with pre-migration schema (no is_notification column)."""
    conn = sqlite3.connect(":memory:")
    extra = ", tool_summary TEXT" if include_tool_summary else ""
    conn.execute(f"""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY, session_id INTEGER, uuid TEXT,
            parent_uuid TEXT, timestamp DATETIME, role TEXT,
            content TEXT NOT NULL, has_tool_use INTEGER DEFAULT 0,
            has_thinking INTEGER DEFAULT 0{extra},
            UNIQUE(session_id, uuid)
        )
    """)
    conn.execute("""
        CREATE TABLE branches (
            id INTEGER PRIMARY KEY, session_id INTEGER, leaf_uuid TEXT,
            fork_point_uuid TEXT, is_active INTEGER DEFAULT 1,
            started_at DATETIME, ended_at DATETIME, exchange_count INTEGER DEFAULT 0,
            files_modified TEXT, commits TEXT, aggregated_content TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE branch_messages (
            branch_id INTEGER, message_id INTEGER, PRIMARY KEY (branch_id, message_id)
        )
    """)
    conn.commit()
    return conn


class TestMigrateColumns:
    def test_adds_tool_summary_column(self):
        """_migrate_columns should add tool_summary and is_notification if missing."""
        conn = _pre_migration_db()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(messages)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "tool_summary" in columns
        assert "is_notification" in columns
        conn.close()

    def test_adds_context_summary_columns(self):
        """_migrate_columns should add context_summary, context_summary_json, summary_version to branches."""
        conn = _pre_migration_db()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(branches)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "context_summary" in columns
        assert "context_summary_json" in columns
        assert "summary_version" in columns
        conn.close()

    def test_idempotent_when_column_exists(self, memory_db):
        """_migrate_columns should not fail when column already exists."""
        _migrate_columns(memory_db)  # Already called in fixture, call again

    def test_migrate_backfills_notifications(self):
        """Migration should flag existing task-notification messages."""
        conn = _pre_migration_db(include_tool_summary=True)
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (1, 1, 'user', 'Hello world')")
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (2, 1, 'assistant', 'Hi there')")
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (3, 1, 'user', '<task-notification><task-id>abc</task-id></task-notification>')")
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (4, 1, 'user', 'Normal follow-up')")
        conn.commit()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT id, is_notification FROM messages ORDER BY id")
        rows = cursor.fetchall()
        assert rows[0] == (1, 0)  # Normal user
        assert rows[1] == (2, 0)  # Assistant
        assert rows[2] == (3, 1)  # Task notification
        assert rows[3] == (4, 0)  # Normal user
        conn.close()

    def test_migrate_reaggregates_branches(self):
        """Migration should re-aggregate branch content excluding notifications."""
        conn = _pre_migration_db(include_tool_summary=True)
        conn.execute("INSERT INTO messages (id, session_id, timestamp, role, content) VALUES (1, 1, '2025-01-01T10:00:00Z', 'user', 'Hello')")
        conn.execute("INSERT INTO messages (id, session_id, timestamp, role, content) VALUES (2, 1, '2025-01-01T10:01:00Z', 'assistant', 'Hi there')")
        conn.execute("INSERT INTO messages (id, session_id, timestamp, role, content) VALUES (3, 1, '2025-01-01T10:02:00Z', 'user', '<task-notification>big agent result</task-notification>')")
        conn.execute("INSERT INTO branches (id, session_id, leaf_uuid, aggregated_content, exchange_count) VALUES (1, 1, 'leaf-1', 'Hello\nHi there\n<task-notification>big agent result</task-notification>', 2)")
        conn.execute("INSERT INTO branch_messages VALUES (1, 1)")
        conn.execute("INSERT INTO branch_messages VALUES (1, 2)")
        conn.execute("INSERT INTO branch_messages VALUES (1, 3)")
        conn.commit()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT aggregated_content, exchange_count FROM branches WHERE id = 1")
        agg, exc = cursor.fetchone()
        assert "<task-notification>" not in agg
        assert "Hello" in agg
        assert "Hi there" in agg
        # exchange_count should be corrected: only 1 real user message
        assert exc == 1
        conn.close()


def _versioned_db(user_version=0, include_is_notification=True):
    """Create in-memory DB with specific user_version for testing versioned migrations."""
    conn = sqlite3.connect(":memory:")
    notif_col = ", is_notification INTEGER DEFAULT 0" if include_is_notification else ""
    conn.execute(f"""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY, session_id INTEGER, uuid TEXT,
            parent_uuid TEXT, timestamp DATETIME, role TEXT,
            content TEXT NOT NULL, tool_summary TEXT,
            has_tool_use INTEGER DEFAULT 0, has_thinking INTEGER DEFAULT 0{notif_col},
            UNIQUE(session_id, uuid)
        )
    """)
    conn.execute("""
        CREATE TABLE branches (
            id INTEGER PRIMARY KEY, session_id INTEGER, leaf_uuid TEXT,
            fork_point_uuid TEXT, is_active INTEGER DEFAULT 1,
            started_at DATETIME, ended_at DATETIME, exchange_count INTEGER DEFAULT 0,
            files_modified TEXT, commits TEXT, aggregated_content TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE branch_messages (
            branch_id INTEGER, message_id INTEGER, PRIMARY KEY (branch_id, message_id)
        )
    """)
    conn.execute(f"PRAGMA user_version = {user_version}")
    conn.commit()
    return conn


class TestVersionedMigration:
    def test_fresh_db_gets_latest_version(self):
        """A fresh DB (no columns, version 0) should end up at user_version = 2."""
        conn = _pre_migration_db()
        _migrate_columns(conn)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == 2
        conn.close()

    def test_v0_to_v2_backfills_both(self):
        """From version 0, both task-notification and teammate messages get backfilled."""
        conn = _versioned_db(user_version=0)
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (1, 1, 'user', 'Hello')")
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (2, 1, 'user', '<task-notification>task</task-notification>')")
        conn.execute("INSERT INTO messages (id, session_id, role, content) VALUES (3, 1, 'user', '<teammate-message teammate_id=\"x\">report</teammate-message>')")
        conn.commit()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT id, is_notification FROM messages ORDER BY id")
        rows = cursor.fetchall()
        assert rows[0] == (1, 0)
        assert rows[1] == (2, 1)
        assert rows[2] == (3, 1)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        conn.close()

    def test_v1_to_v2_backfills_only_teammate(self):
        """From version 1, only teammate messages get backfilled (task-notifications already done)."""
        conn = _versioned_db(user_version=1)
        # Simulate a DB where task-notifications were already flagged by version 1
        conn.execute("INSERT INTO messages (id, session_id, role, content, is_notification) VALUES (1, 1, 'user', '<task-notification>task</task-notification>', 1)")
        conn.execute("INSERT INTO messages (id, session_id, role, content, is_notification) VALUES (2, 1, 'user', '<teammate-message teammate_id=\"x\">report</teammate-message>', 0)")
        conn.execute("INSERT INTO messages (id, session_id, role, content, is_notification) VALUES (3, 1, 'user', 'Normal message', 0)")
        conn.commit()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT id, is_notification FROM messages ORDER BY id")
        rows = cursor.fetchall()
        assert rows[0] == (1, 1)  # Already flagged, untouched
        assert rows[1] == (2, 1)  # Newly flagged by version 2
        assert rows[2] == (3, 0)  # Normal, untouched
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        conn.close()

    def test_v2_skips_all_migrations(self):
        """From version 2, no migrations run."""
        conn = _versioned_db(user_version=2)
        conn.execute("INSERT INTO messages (id, session_id, role, content, is_notification) VALUES (1, 1, 'user', '<teammate-message>should stay 0</teammate-message>', 0)")
        conn.commit()

        _migrate_columns(conn)

        # Should NOT have been flagged (migration already ran)
        cursor = conn.cursor()
        cursor.execute("SELECT is_notification FROM messages WHERE id = 1")
        assert cursor.fetchone()[0] == 0
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        conn.close()


class TestLoadSettings:
    def test_always_returns_defaults(self):
        """load_settings always returns hardcoded defaults (YAML was removed)."""
        settings = load_settings()
        assert settings == DEFAULT_SETTINGS

    def test_returns_copy(self):
        """Each call should return a fresh copy, not a reference."""
        s1 = load_settings()
        s2 = load_settings()
        s1["max_context_sessions"] = 99
        assert s2["max_context_sessions"] == 2

    def test_default_values(self):
        assert DEFAULT_SETTINGS["auto_inject_context"] is True
        assert DEFAULT_SETTINGS["max_context_sessions"] == 2
        assert DEFAULT_SETTINGS["logging_enabled"] is False
        assert DEFAULT_SETTINGS["sync_on_stop"] is True
        assert isinstance(DEFAULT_SETTINGS["exclude_projects"], list)


class TestMigrateDb:
    """Test migrate_db — v2 schema detection and DB replacement."""

    def test_fresh_db_no_tables(self):
        """A fresh DB with no tables should return False (no migration needed)."""
        conn = sqlite3.connect(":memory:")
        result = migrate_db(conn)
        assert result is False

    def test_v3_db_no_migration(self):
        """A DB with branches table (v3) should return False."""
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA)
        conn.commit()
        result = migrate_db(conn)
        assert result is False

    def test_v2_db_file_migrated(self):
        """A file-backed DB with sessions but no branches (v2) should be deleted and recreated."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            # Create a v2-style DB (sessions exists, branches doesn't)
            conn = sqlite3.connect(str(db_path))
            conn.execute("""
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY,
                    uuid TEXT UNIQUE NOT NULL,
                    project_id INTEGER
                )
            """)
            conn.execute("INSERT INTO sessions (uuid) VALUES ('old-session')")
            conn.commit()

            result = migrate_db(conn)
            assert result is True, "Should detect v2 schema and migrate"

            # Old DB should have been deleted and recreated with v3 schema
            # Verify new schema has branches table
            new_conn = sqlite3.connect(str(db_path))
            cursor = new_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branches'")
            assert cursor.fetchone() is not None, "Recreated DB should have branches table"

            # Old session should be gone (DB was nuked)
            cursor.execute("SELECT COUNT(*) FROM sessions")
            assert cursor.fetchone()[0] == 0, "Old data should be gone after migration"
            new_conn.close()
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_v2_in_memory_migrated(self):
        """An in-memory DB with v2 schema should return True and handle gracefully."""
        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()

        result = migrate_db(conn)
        assert result is True, "Should detect v2 schema in memory DB"
