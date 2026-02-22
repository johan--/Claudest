#!/usr/bin/env python3
"""Run project validation before committing.

Detects project type from the root directory and runs the appropriate
linter or build check. Returns structured pass/fail output.

Exit codes:
  0 — validation passed
  1 — validation failed (see output for details)
  2 — no validator found for this project type

Usage:
  validate.py <project-root> [--output text|json]

Examples:
  validate.py .
  validate.py /path/to/project --output json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


VALIDATORS = [
    {
        "marker": "Cargo.toml",
        "tool": "cargo",
        "cmd": ["cargo", "fmt", "--check"],
        "fallback_cmd": ["cargo", "build"],
    },
    {
        "marker": "package.json",
        "tool": "npm",
        "cmd": ["npm", "run", "lint", "--if-present"],
        "fallback_cmd": None,
    },
    {
        "marker": "pyproject.toml",
        "tool": "ruff",
        "cmd": ["ruff", "check", "."],
        "fallback_cmd": None,
    },
]


def detect_validator(root: Path) -> dict | None:
    for v in VALIDATORS:
        if (root / v["marker"]).exists():
            return v
    return None


def run_command(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_root", help="Path to project root directory")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        msg = f"Not a directory: {root}"
        if args.output == "json":
            print(json.dumps({"valid": False, "tool": None, "output": msg}))
        else:
            print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)

    validator = detect_validator(root)
    if validator is None:
        msg = "No validator found (no Cargo.toml, package.json, or pyproject.toml)"
        if args.output == "json":
            print(json.dumps({"valid": False, "tool": None, "output": msg}))
        else:
            print(msg)
        sys.exit(2)

    tool = validator["tool"]
    valid, output = run_command(validator["cmd"], root)

    # If primary command not found, try fallback; if no fallback, treat as no validator
    if not valid and "not found" in output:
        if validator.get("fallback_cmd"):
            valid, output = run_command(validator["fallback_cmd"], root)
            if not valid and "not found" in output:
                # Fallback also missing — tool chain not installed
                msg = f"{tool} not installed; skipping validation"
                if args.output == "json":
                    print(json.dumps({"valid": False, "tool": tool, "output": msg}))
                else:
                    print(msg)
                sys.exit(2)
        else:
            msg = f"{tool} not installed; skipping validation"
            if args.output == "json":
                print(json.dumps({"valid": False, "tool": tool, "output": msg}))
            else:
                print(msg)
            sys.exit(2)

    if args.output == "json":
        print(json.dumps({"valid": valid, "tool": tool, "output": output}))
    else:
        status = "passed" if valid else "failed"
        print(f"Validation {status} ({tool})")
        if output:
            print(output)

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
