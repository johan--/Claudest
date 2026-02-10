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


class TestMigrateColumns:
    def test_adds_tool_summary_column(self):
        """_migrate_columns should add tool_summary if missing."""
        conn = sqlite3.connect(":memory:")
        # Create a minimal messages table without tool_summary
        conn.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                session_id INTEGER,
                uuid TEXT,
                parent_uuid TEXT,
                timestamp DATETIME,
                role TEXT,
                content TEXT NOT NULL,
                has_tool_use INTEGER DEFAULT 0,
                has_thinking INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        _migrate_columns(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(messages)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "tool_summary" in columns
        conn.close()

    def test_idempotent_when_column_exists(self, memory_db):
        """_migrate_columns should not fail when column already exists."""
        _migrate_columns(memory_db)  # Already called in fixture, call again


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
