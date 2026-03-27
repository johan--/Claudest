#!/usr/bin/env python3
"""SessionStart hook - setup memory directory and trigger initial import."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "skills" / "recall-conversations" / "scripts"))

from memory_lib.db import DEFAULT_DB_PATH


def _spawn_background(script_name: str) -> None:
    """Spawn a script as a detached background process."""
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        **kwargs
    )


def _needs_backfill() -> bool:
    """Check if any branches need summary backfill. Returns False on any error."""
    try:
        import sqlite3
        conn = sqlite3.connect(str(DEFAULT_DB_PATH))
        conn.execute("PRAGMA busy_timeout = 2000")
        # Check column exists before querying
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(branches)")
        cols = {row[1] for row in cursor.fetchall()}
        if "summary_version" not in cols:
            conn.close()
            return False
        cursor.execute(
            "SELECT COUNT(*) FROM branches WHERE summary_version IS NULL OR summary_version = 0"
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def main():
    try:
        # Create directory
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Run initial import in background if DB doesn't exist
        if not DEFAULT_DB_PATH.exists():
            _spawn_background("import_conversations.py")
        elif _needs_backfill():
            _spawn_background("backfill_summaries.py")
    except Exception:
        pass

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
