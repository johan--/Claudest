#!/usr/bin/env python3
"""
UserPromptSubmit hook — detects /clear or /new and writes a handoff file
so the subsequent SessionStart hook can hard-link to this session.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "skills" / "recall-conversations" / "scripts"))

from memory_lib.db import get_db_path, load_settings


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"continue": True}))
        return

    prompt = hook_input.get("prompt", "")
    session_id = hook_input.get("session_id")
    cwd = hook_input.get("cwd")

    # Detect /clear or /new — prompt may be plain text or XML-wrapped command
    # e.g. "<command-name>/clear</command-name>\n<command-message>clear</command-message>"
    stripped = prompt.strip()
    is_clear = (
        stripped in ("/clear", "/new")
        or "<command-name>/clear</command-name>" in prompt
        or "<command-name>/new</command-name>" in prompt
    )
    if not is_clear:
        print(json.dumps({"continue": True}))
        return

    if not session_id or not cwd:
        print(json.dumps({"continue": True}))
        return

    settings = load_settings()
    db_path = get_db_path(settings)
    handoff_path = db_path.parent / "clear-handoff.json"

    handoff = {
        "session_id": session_id,
        "cwd": cwd,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        handoff_path.write_text(json.dumps(handoff))
    except OSError:
        pass

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
