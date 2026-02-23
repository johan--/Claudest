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


def main():
    try:
        # Create directory
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Run initial import in background if DB doesn't exist
        if not DEFAULT_DB_PATH.exists():
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            if sys.platform == "win32":
                kwargs["creationflags"] = (
                    subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen(
                [sys.executable, str(SCRIPT_DIR / "import_conversations.py")],
                **kwargs
            )
    except Exception:
        pass

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
