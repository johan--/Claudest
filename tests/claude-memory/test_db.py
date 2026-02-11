"""Tests for memory_lib.db — schema creation, migration, settings."""

import sqlite3

import pytest

from memory_lib.db import (
    DEFAULT_SETTINGS,
    SCHEMA,
    _migrate_columns,
    load_settings,
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

    def test_views_exist(self, memory_db):
        cursor = memory_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        views = {row[0] for row in cursor.fetchall()}
        assert "search_results" in views
        assert "recent_conversations" in views

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


class TestLoadSettings:
    def test_missing_file_returns_defaults(self, tmp_path):
        settings = load_settings(tmp_path / "nonexistent.md")
        assert settings == DEFAULT_SETTINGS

    def test_default_values(self):
        assert DEFAULT_SETTINGS["auto_inject_context"] is True
        assert DEFAULT_SETTINGS["max_context_sessions"] == 2
        assert DEFAULT_SETTINGS["logging_enabled"] is False
        assert DEFAULT_SETTINGS["sync_on_stop"] is True
        assert isinstance(DEFAULT_SETTINGS["exclude_projects"], list)

    def test_yaml_frontmatter_parsed(self, tmp_path):
        """Settings from YAML frontmatter should override defaults."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        settings_file = tmp_path / "settings.local.md"
        settings_file.write_text(
            "---\n"
            "max_context_sessions: 5\n"
            "logging_enabled: true\n"
            "---\n"
            "# Settings\n"
            "Some documentation here.\n"
        )
        settings = load_settings(settings_file)
        assert settings["max_context_sessions"] == 5
        assert settings["logging_enabled"] is True
        # Non-overridden defaults should persist
        assert settings["auto_inject_context"] is True

    def test_invalid_yaml_returns_defaults(self, tmp_path):
        """Malformed YAML should fall back to defaults."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        settings_file = tmp_path / "settings.local.md"
        settings_file.write_text("---\n: : invalid:\n---\n")
        settings = load_settings(settings_file)
        # Should not crash, returns defaults (possibly with partial parse)
        assert isinstance(settings, dict)
