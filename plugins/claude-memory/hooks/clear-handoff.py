#!/usr/bin/env python3
"""SessionEnd hook (matcher: clear) — writes handoff file for SessionStart to link sessions."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "skills" / "recall-conversations" / "scripts"))

from memory_lib.db import get_db_path, load_settings

LOG_PATH = Path.home() / ".claude-memory" / "clear-handoff.log"


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with LOG_PATH.open("a") as f:
            f.write(f"[{ts}] {msg}\n")
    except OSError:
        pass


def main():
    raw = sys.stdin.read()
    try:
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, EOFError):
        return

    session_id = hook_input.get("session_id")
    cwd = hook_input.get("cwd")
    _log(f"fired. session={session_id} cwd={cwd}")

    if not session_id or not cwd:
        return

    settings = load_settings()
    db_path = get_db_path(settings)
    handoff_path = db_path.parent / "clear-handoff.json"

    handoff_path.write_text(json.dumps({
        "session_id": session_id,
        "cwd": cwd,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }))
    _log(f"handoff written. session={session_id}")


if __name__ == "__main__":
    main()
