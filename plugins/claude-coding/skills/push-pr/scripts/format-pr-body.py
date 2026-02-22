#!/usr/bin/env python3
"""Generate a formatted PR body from git commit history and diff stats.

Compares HEAD against a base branch and produces a markdown PR description
with summary, changes, and commit list sections.

Usage:
  format-pr-body.py [--base BRANCH] [--output text|json]

Examples:
  format-pr-body.py --base main
  format-pr-body.py --base feat/auth --output json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def run_git(args: list[str]) -> tuple[str, int]:
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def get_commits(base: str) -> list[tuple[str, str]]:
    out, code = run_git(["log", f"{base}..HEAD", "--oneline"])
    if code != 0 or not out:
        return []
    commits = []
    for line in out.splitlines():
        if line:
            sha, _, msg = line.partition(" ")
            commits.append((sha, msg))
    return commits


def get_diff_stat(base: str) -> str:
    out, _ = run_git(["diff", f"{base}...HEAD", "--stat"])
    return out


def get_changed_files(base: str) -> list[dict]:
    out, code = run_git(["diff", f"{base}...HEAD", "--name-status"])
    if code != 0 or not out:
        return []
    files = []
    for line in out.splitlines():
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            files.append({"status": parts[0], "path": parts[1]})
    return files


GENERATED_SUFFIXES = (".lock", ".sum", ".min.js", ".min.css", "-lock.json")
SKIP_PATHS = ("__pycache__", ".pyc", "node_modules", "dist/", "build/")


def is_significant(path: str) -> bool:
    if any(path.endswith(s) for s in GENERATED_SUFFIXES):
        return False
    if any(p in path for p in SKIP_PATHS):
        return False
    return True


def format_body(
    commits: list[tuple[str, str]],
    diff_stat: str,
    files: list[dict],
) -> str:
    if commits:
        summary = "\n".join(f"- {msg}" for _, msg in commits[:6])
        if len(commits) > 6:
            summary += f"\n- _{len(commits) - 6} more commits_"
    else:
        summary = "- No commits found"

    significant = [f for f in files if is_significant(f["path"])][:10]
    if significant:
        changes = "\n".join(f"- `{f['path']}`" for f in significant)
        omitted = len(files) - len(significant)
        if omitted > 0:
            changes += f"\n- _{omitted} generated/lock files omitted_"
    else:
        changes = "- See diff stat"

    commit_list = "\n".join(f"- `{sha}` {msg}" for sha, msg in commits)

    body = (
        f"## Summary\n{summary}\n\n"
        f"## Changes\n{changes}\n\n"
        f"## Commits\n{commit_list}"
    )
    if diff_stat:
        body += f"\n\n## Diff Stat\n```\n{diff_stat}\n```"

    return body


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base", default="main",
        help="Base branch to compare against (default: main)",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format: text (default) or json with title + body fields",
    )
    args = parser.parse_args()

    commits = get_commits(args.base)
    diff_stat = get_diff_stat(args.base)
    files = get_changed_files(args.base)

    if not commits and not files:
        print(f"No changes found relative to '{args.base}'.", file=sys.stderr)
        sys.exit(1)

    body = format_body(commits, diff_stat, files)

    if args.output == "json":
        title = commits[0][1] if commits else "Update"
        print(json.dumps({"title": title, "body": body}))
    else:
        print(body)

    sys.exit(0)


if __name__ == "__main__":
    main()
