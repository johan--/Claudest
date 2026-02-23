#!/usr/bin/env python3
"""Multi-platform video research toolkit powered by yt-dlp.

Usage:
  yt_research.py [global flags] <subcommand> [args]
  yt_research.py search <query> [flags]
  yt_research.py metadata <url> [flags]
  yt_research.py transcript <url> [flags]
  yt_research.py audio <url> [flags]
  yt_research.py channel <url|@handle> [flags]

Examples:
  yt_research.py search "python async tutorial" --count 5
  yt_research.py transcript "https://youtube.com/watch?v=abc" --save -t ml
  yt_research.py channel "@ThePrimeagen" --limit 30
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.1.0"
DEFAULT_DIR = Path.home() / "youtube-research"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sanitize_title(title: str) -> str:
    """Sanitize a string for use as a filename."""
    title = re.sub(r'[/:\\?\"<>|*]', "-", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title[:200]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def log(msg: str, quiet: bool = False) -> None:
    """Print diagnostic message to stderr (suppressed by --quiet)."""
    if not quiet:
        print(msg, file=sys.stderr)


def find_ytdlp() -> str:
    """Return path to yt-dlp binary or exit 2."""
    path = shutil.which("yt-dlp")
    if path:
        return path
    log("Error: yt-dlp not found. Install with: pip install yt-dlp")
    sys.exit(2)


def run_ytdlp(
    args: list,
    cookies: str | None = None,
    quiet: bool = False,
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    """Invoke yt-dlp and return the CompletedProcess."""
    cmd = [find_ytdlp()] + args
    if cookies:
        cmd.extend(["--cookies-from-browser", cookies])
    if quiet:
        cmd.extend(["--quiet", "--no-warnings"])
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f"Error: yt-dlp timed out after {timeout}s")
        sys.exit(3)
    except FileNotFoundError:
        log("Error: yt-dlp not found")
        sys.exit(2)


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

def format_entry(entry: dict, channel_fallback: str = "") -> dict:
    """Normalize a yt-dlp entry dict to the standard result shape.

    channel_fallback is used when per-entry channel is None (e.g. flat-playlist
    on channel pages where the channel is implicit from the playlist URL).
    """
    return {
        "id": entry.get("id") or "",
        "title": entry.get("title") or "",
        "channel": entry.get("channel") or entry.get("uploader") or channel_fallback,
        "duration": entry.get("duration"),
        "duration_string": entry.get("duration_string") or "",
        "view_count": entry.get("view_count"),
        "upload_date": entry.get("upload_date") or "",
        "url": entry.get("webpage_url") or entry.get("url") or "",
        "description": (entry.get("description") or "")[:500],
    }


def entries_to_text(entries: list) -> str:
    """Render a list of entry dicts as numbered human-readable text."""
    lines = []
    for i, e in enumerate(entries, 1):
        dur = e.get("duration_string") or ""
        views = e.get("view_count")
        view_str = f" | {views:,} views" if views else ""
        lines.append(f"{i}. {e['title']}")
        lines.append(f"   {e['channel']} | {dur}{view_str}")
        lines.append(f"   {e['url']}")
        lines.append("")
    return "\n".join(lines)


def output_result(data, fmt: str) -> None:
    """Print data in the requested format."""
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif isinstance(data, list):
        print(entries_to_text(data))
    elif isinstance(data, dict):
        for key, val in data.items():
            if key == "chapters" and val:
                print("chapters:")
                for ch in val:
                    print(f"  {ch['start_time']:.0f}s-{ch['end_time']:.0f}s: {ch['title']}")
            elif key == "description":
                desc = val[:300] + ("..." if len(val) > 300 else "")
                print(f"description: {desc}")
            elif isinstance(val, list):
                print(f"{key}: {', '.join(str(v) for v in val)}")
            else:
                print(f"{key}: {val}")
    else:
        print(data)


# ---------------------------------------------------------------------------
# VTT / SRT transcript cleaning
# ---------------------------------------------------------------------------

def clean_vtt(content: str, keep_timestamps: bool = False) -> str:
    """Convert VTT/SRT content to clean text or normalized SRT."""
    lines = content.split("\n")
    if keep_timestamps:
        return _to_srt(lines)
    return _to_plain(lines)


def _to_plain(lines: list) -> str:
    """Strip VTT to deduplicated plain text."""
    seen: set = set()
    result: list = []
    for raw in lines:
        line = raw.strip()
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or "-->" in line
            or re.match(r"^\d+$", line)
        ):
            continue
        clean = re.sub(r"<[^>]*>", "", line)
        clean = (
            clean.replace("&amp;", "&")
            .replace("&gt;", ">")
            .replace("&lt;", "<")
            .replace("&nbsp;", " ")
            .replace("&quot;", '"')
            .replace("\\h", " ")
        )
        # Collapse multiple spaces from \h replacements
        clean = re.sub(r" {2,}", " ", clean).strip()
        if clean and clean not in seen:
            result.append(clean)
            seen.add(clean)
    return "\n".join(result)


def _to_srt(lines: list) -> str:
    """Convert VTT lines to SRT format preserving timestamps.

    Auto-generated captions use a scrolling window where each cue repeats
    the previous line plus appends a new one. We deduplicate by tracking
    the previous cue's text and only emitting lines that are new.
    """
    result: list = []
    counter = 0
    prev_texts: list = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            ts = line.replace(".", ",")
            i += 1
            cur_texts: list = []
            while i < len(lines) and lines[i].strip():
                text = re.sub(r"<[^>]*>", "", lines[i].strip())
                text = (
                    text.replace("&amp;", "&")
                    .replace("&gt;", ">")
                    .replace("&lt;", "<")
                    .replace("\\h", " ")
                )
                text = re.sub(r" {2,}", " ", text).strip()
                if text:
                    cur_texts.append(text)
                i += 1
            # Only keep lines not already shown in the previous cue
            new_texts = [t for t in cur_texts if t not in prev_texts]
            if new_texts:
                counter += 1
                result.append(str(counter))
                result.append(ts)
                result.extend(new_texts)
                result.append("")
            prev_texts = cur_texts
        else:
            i += 1
    return "\n".join(result)


# ---------------------------------------------------------------------------
# Subcommand: search
# ---------------------------------------------------------------------------

class ResearchError(Exception):
    """Raised by handlers; carries an exit code."""

    def __init__(self, message: str, code: int = 3):
        super().__init__(message)
        self.code = code


def cmd_search(args, g):
    """Search YouTube for videos matching a query."""
    query = args.query
    count = min(args.count, 50)

    has_filters = any(
        [args.min_duration, args.max_duration, args.after, args.before, args.min_views]
    )
    fetch_count = min(count * 2, 50) if has_filters else count

    if g.dry_run:
        print(f'yt-dlp --flat-playlist --dump-single-json "ytsearch{fetch_count}:{query}"')
        return

    log(f"Searching: {query} (fetching {fetch_count})...", g.quiet)

    result = run_ytdlp(
        ["--flat-playlist", "--dump-single-json", f"ytsearch{fetch_count}:{query}"],
        cookies=g.cookies,
        quiet=True,
    )

    if result.returncode != 0:
        raise ResearchError(f"yt-dlp search failed: {result.stderr.strip()}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ResearchError("Failed to parse yt-dlp output")

    entries = [format_entry(e) for e in data.get("entries", [])]

    # Client-side filtering
    if args.min_duration:
        entries = [e for e in entries if (e.get("duration") or 0) >= args.min_duration]
    if args.max_duration:
        entries = [e for e in entries if (e.get("duration") or 0) <= args.max_duration]
    if args.after:
        entries = [e for e in entries if (e.get("upload_date") or "") >= args.after]
    if args.before:
        entries = [e for e in entries if (e.get("upload_date") or "") <= args.before]
    if args.min_views:
        entries = [e for e in entries if (e.get("view_count") or 0) >= args.min_views]

    entries = entries[:count]

    if not entries:
        raise ResearchError("No results found matching criteria.", 4)

    fmt = g.format or "json"
    output_result(entries, fmt)


# ---------------------------------------------------------------------------
# Subcommand: metadata
# ---------------------------------------------------------------------------

def cmd_metadata(args, g):
    """Extract full metadata for a video or playlist."""
    url = args.url

    ytdlp_args = (
        ["--flat-playlist", "--dump-single-json"]
        if args.playlist
        else ["--dump-json", "--skip-download"]
    )

    if g.dry_run:
        print(f'yt-dlp {" ".join(ytdlp_args)} "{url}"')
        return

    log(f"Extracting metadata: {url}...", g.quiet)

    result = run_ytdlp(ytdlp_args + [url], cookies=g.cookies, quiet=True)
    if result.returncode != 0:
        raise ResearchError(f"yt-dlp failed: {result.stderr.strip()}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ResearchError("Failed to parse yt-dlp output")

    fmt = g.format or "json"

    if args.playlist:
        entries = [format_entry(e) for e in data.get("entries", [])]
        output_result(entries, fmt)
    else:
        meta = {
            "id": data.get("id", ""),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "channel": data.get("channel") or data.get("uploader", ""),
            "channel_url": data.get("channel_url", ""),
            "duration": data.get("duration"),
            "duration_string": data.get("duration_string", ""),
            "upload_date": data.get("upload_date", ""),
            "view_count": data.get("view_count"),
            "like_count": data.get("like_count"),
            "comment_count": data.get("comment_count"),
            "tags": data.get("tags", []),
            "categories": data.get("categories", []),
            "chapters": [
                {
                    "title": c.get("title", ""),
                    "start_time": c.get("start_time", 0),
                    "end_time": c.get("end_time", 0),
                }
                for c in (data.get("chapters") or [])
            ],
            "thumbnail_url": data.get("thumbnail", ""),
            "subtitle_languages": sorted(
                set(
                    list((data.get("subtitles") or {}).keys())
                    + list((data.get("automatic_captions") or {}).keys())
                )
            ),
            "url": data.get("webpage_url", ""),
        }
        output_result(meta, fmt)


# ---------------------------------------------------------------------------
# Subcommand: transcript
# ---------------------------------------------------------------------------

def cmd_transcript(args, g):
    """Download and clean transcript for a video."""
    url = args.url
    lang = args.lang

    # List available languages
    if lang == "all":
        if g.dry_run:
            print(f'yt-dlp --dump-json --skip-download "{url}"')
            return

        log(f"Listing subtitles for: {url}...", g.quiet)
        result = run_ytdlp(
            ["--dump-json", "--skip-download", url], cookies=g.cookies, quiet=True
        )
        if result.returncode != 0:
            raise ResearchError(f"yt-dlp failed: {result.stderr.strip()}")

        data = json.loads(result.stdout)
        info = {
            "manual_subtitles": sorted((data.get("subtitles") or {}).keys()),
            "auto_generated": sorted((data.get("automatic_captions") or {}).keys()),
        }
        print(json.dumps(info, indent=2))
        return

    if g.dry_run:
        print(
            f'yt-dlp --write-subs --write-auto-subs --sub-langs "{lang}" '
            f'--convert-subs srt --skip-download "{url}"'
        )
        return

    log(f"Downloading transcript ({lang}): {url}...", g.quiet)

    with tempfile.TemporaryDirectory() as tmpdir:
        sub_file = None

        # Try manual subs first, then auto-generated
        for flag in ["--write-subs", "--write-auto-subs"]:
            run_ytdlp(
                [
                    flag,
                    "--sub-langs", lang,
                    "--convert-subs", "srt",
                    "--skip-download",
                    "-o", os.path.join(tmpdir, "%(id)s"),
                    url,
                ],
                cookies=g.cookies,
                quiet=True,
            )
            found = [f for f in os.listdir(tmpdir) if f.endswith((".srt", ".vtt"))]
            if found:
                sub_file = os.path.join(tmpdir, found[0])
                break

        if not sub_file:
            raise ResearchError(
                f"No subtitles available in '{lang}'. Use --lang all to list available.",
                4,
            )

        with open(sub_file, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()

        cleaned = clean_vtt(raw, keep_timestamps=args.timestamps)

        if args.save:
            title_r = run_ytdlp(
                ["--print", "%(title)s", "--skip-download", url],
                cookies=g.cookies,
                quiet=True,
            )
            title = sanitize_title(title_r.stdout.strip() or "transcript")
            ext = ".srt" if args.timestamps else ".txt"
            out_dir = ensure_dir(Path(g.dir) / g.topic)
            out_path = out_dir / f"{title}{ext}"
            out_path.write_text(cleaned, encoding="utf-8")
            print(str(out_path))
            log(f"Saved to: {out_path}", g.quiet)
        else:
            print(cleaned)


# ---------------------------------------------------------------------------
# Subcommand: audio
# ---------------------------------------------------------------------------

def cmd_audio(args, g):
    """Download audio from a video."""
    url = args.url
    audio_fmt = args.audio_format
    quality = args.quality

    if g.dry_run:
        print(
            f'yt-dlp -x --audio-format {audio_fmt} --audio-quality {quality} "{url}"'
        )
        return

    log(f"Downloading audio: {url}...", g.quiet)

    # Get title for filename
    title_r = run_ytdlp(
        ["--print", "%(title)s", "--skip-download", url],
        cookies=g.cookies,
        quiet=True,
    )
    title = sanitize_title(title_r.stdout.strip() or "audio")

    out_dir = ensure_dir(Path(g.dir) / g.topic / "audio")
    out_template = str(out_dir / f"{title}.%(ext)s")

    result = run_ytdlp(
        [
            "-x",
            "--audio-format", audio_fmt,
            "--audio-quality", quality,
            "-o", out_template,
            url,
        ],
        cookies=g.cookies,
        quiet=g.quiet,
        timeout=600,
    )

    if result.returncode != 0:
        raise ResearchError(f"Audio download failed: {result.stderr.strip()}")

    # Find the actual output file (extension may vary)
    matches = sorted(out_dir.glob(f"{title}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    saved = matches[0] if matches else out_dir / f"{title}.{audio_fmt}"
    print(str(saved))
    log(f"Saved to: {saved}", g.quiet)


# ---------------------------------------------------------------------------
# Subcommand: channel
# ---------------------------------------------------------------------------

def cmd_channel(args, g):
    """Scan a channel's videos, shorts, streams, or playlists."""
    raw = args.url
    tab = args.tab

    # Expand @handle → full URL
    if raw.startswith("@"):
        url = f"https://www.youtube.com/{raw}/{tab}"
    elif "youtube.com" in raw and f"/{tab}" not in raw:
        url = raw.rstrip("/") + "/" + tab
    else:
        url = raw

    has_filters = args.after or args.before
    fetch_limit = args.limit * 2 if has_filters else args.limit

    if g.dry_run:
        print(
            f'yt-dlp --flat-playlist --dump-single-json '
            f'--playlist-items "1:{fetch_limit}" "{url}"'
        )
        return

    log(f"Scanning channel: {url} (limit {fetch_limit})...", g.quiet)

    result = run_ytdlp(
        [
            "--flat-playlist",
            "--dump-single-json",
            "--playlist-items", f"1:{fetch_limit}",
            url,
        ],
        cookies=g.cookies,
        quiet=True,
    )

    if result.returncode != 0:
        raise ResearchError(f"yt-dlp failed: {result.stderr.strip()}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ResearchError("Failed to parse yt-dlp output")

    # Channel name is on the playlist object, not per-entry in flat mode
    ch_name = data.get("channel") or data.get("uploader") or ""
    entries = [format_entry(e, channel_fallback=ch_name) for e in data.get("entries", [])]

    if args.after:
        entries = [e for e in entries if (e.get("upload_date") or "") >= args.after]
    if args.before:
        entries = [e for e in entries if (e.get("upload_date") or "") <= args.before]

    if args.sort == "views":
        entries.sort(key=lambda e: e.get("view_count") or 0, reverse=True)

    entries = entries[: args.limit]

    if not entries:
        raise ResearchError("No videos found matching criteria.", 4)

    fmt = g.format or "json"
    output_result(entries, fmt)


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def run_batch(handler, urls: list, args, g):
    """Run a handler for each URL, collecting results."""
    results = []
    errors = []

    for raw_url in urls:
        url = raw_url.strip()
        if not url or url.startswith("#") or url.startswith(";"):
            continue

        args.url = url
        old_stdout = sys.stdout
        sys.stdout = buf = io.StringIO()

        try:
            handler(args, g)
            output = buf.getvalue()
        except ResearchError as exc:
            sys.stdout = old_stdout
            errors.append({"url": url, "error": str(exc), "code": exc.code})
            log(f"Failed: {url} — {exc}", g.quiet)
            continue
        finally:
            sys.stdout = old_stdout

        fmt = g.format or "json"
        if fmt == "json":
            try:
                results.append(json.loads(output))
            except json.JSONDecodeError:
                results.append(output.strip())
        else:
            results.append(output.strip())

    if not results:
        log("All URLs failed.")
        sys.exit(3)

    fmt = g.format or "json"
    if fmt == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for i, r in enumerate(results):
            if i > 0:
                print(f"\n--- next ---\n")
            print(r)

    if errors:
        log(
            f"\n{len(errors)} of {len(errors) + len(results)} URLs failed.",
            g.quiet,
        )


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _add_global_flags(p: argparse.ArgumentParser) -> None:
    """Add global flags to a parser (called on each subparser)."""
    p.add_argument(
        "-f", "--format", choices=["json", "text"], default=None,
        help="Output format (default: json for search/metadata/channel, text for transcript)",
    )
    p.add_argument(
        "-t", "--topic", default="general",
        help="Topic subdirectory for saved files (default: general)",
    )
    p.add_argument(
        "-d", "--dir", default=None,
        help="Base output directory (default: ~/youtube-research)",
    )
    p.add_argument(
        "--cookies", default=None, metavar="BROWSER",
        help="Browser for cookie auth (chrome, firefox, safari, brave, edge)",
    )
    p.add_argument("-q", "--quiet", action="store_true",
                   help="Suppress progress messages on stderr")
    p.add_argument("--dry-run", action="store_true",
                   help="Show yt-dlp command without executing")
    p.add_argument(
        "-b", "--batch", default=None, metavar="FILE",
        help="Read URLs from file (one per line). Use - for stdin.",
    )
    p.add_argument("--no-color", action="store_true", help="Disable colored output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt_research.py",
        description="Multi-platform video research toolkit powered by yt-dlp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            '  %(prog)s search "python async tutorial" --count 5\n'
            '  %(prog)s transcript "https://youtube.com/watch?v=abc" --save -t ml\n'
            "  %(prog)s channel @ThePrimeagen --limit 30\n"
            '  %(prog)s transcript --batch urls.txt --save -t talks\n'
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subs = parser.add_subparsers(dest="command", help="subcommands")

    # -- search --
    p_s = subs.add_parser("search", help="Search YouTube for videos")
    _add_global_flags(p_s)
    p_s.add_argument("query", help="Search query string")
    p_s.add_argument(
        "--count", type=int, default=10, help="Max results (default: 10, max: 50)"
    )
    p_s.add_argument("--min-duration", type=int, default=None, metavar="SECS")
    p_s.add_argument("--max-duration", type=int, default=None, metavar="SECS")
    p_s.add_argument("--after", default=None, metavar="YYYYMMDD")
    p_s.add_argument("--before", default=None, metavar="YYYYMMDD")
    p_s.add_argument("--min-views", type=int, default=None)

    # -- metadata --
    p_m = subs.add_parser("metadata", help="Extract video/playlist metadata")
    _add_global_flags(p_m)
    p_m.add_argument("url", help="Video or playlist URL")
    p_m.add_argument(
        "--playlist", action="store_true",
        help="Treat as playlist; return flat entry list",
    )

    # -- transcript --
    p_t = subs.add_parser("transcript", help="Download and clean transcript")
    _add_global_flags(p_t)
    p_t.add_argument("url", nargs="?", help="Video URL")
    p_t.add_argument(
        "-l", "--lang", default="en",
        help="Subtitle language (default: en; 'all' to list)",
    )
    p_t.add_argument(
        "--timestamps", action="store_true",
        help="Preserve SRT timestamps instead of plain text",
    )
    p_t.add_argument("--save", action="store_true",
                     help="Save to file in topic directory")

    # -- audio --
    p_a = subs.add_parser("audio", help="Download audio from video")
    _add_global_flags(p_a)
    p_a.add_argument("url", nargs="?", help="Video URL")
    p_a.add_argument(
        "--audio-format", default="mp3",
        choices=["mp3", "m4a", "opus", "wav"],
        help="Audio format (default: mp3)",
    )
    p_a.add_argument("--quality", default="192K",
                     help="Audio quality/bitrate (default: 192K)")

    # -- channel --
    p_c = subs.add_parser("channel", help="Scan channel videos/playlists")
    _add_global_flags(p_c)
    p_c.add_argument("url", help="Channel URL or @handle")
    p_c.add_argument("--limit", type=int, default=20,
                     help="Max entries (default: 20)")
    p_c.add_argument(
        "--tab", default="videos",
        choices=["videos", "shorts", "streams", "playlists"],
    )
    p_c.add_argument("--after", default=None, metavar="YYYYMMDD")
    p_c.add_argument("--before", default=None, metavar="YYYYMMDD")
    p_c.add_argument("--sort", default="date", choices=["date", "views"],
                     help="Sort order")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

HANDLERS = {
    "search": cmd_search,
    "metadata": cmd_metadata,
    "transcript": cmd_transcript,
    "audio": cmd_audio,
    "channel": cmd_channel,
}


def main() -> None:
    parser = build_parser()

    # Handle bare invocation with no subcommand
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        parser.print_help()
        if len(sys.argv) < 2:
            sys.exit(1)
        sys.exit(0)
    if sys.argv[1] == "--version":
        parser.parse_args(["--version"])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Resolve defaults from env
    if args.dir is None:
        args.dir = os.environ.get("YT_RESEARCH_DIR", str(DEFAULT_DIR))
    if args.topic == "general":
        args.topic = os.environ.get("YT_RESEARCH_TOPIC", "general")
    if args.cookies is None:
        args.cookies = os.environ.get("YT_RESEARCH_COOKIES")

    # Set default format per subcommand
    if args.format is None and args.command == "transcript":
        args.format = "text"

    handler = HANDLERS[args.command]

    try:
        if args.batch and args.command != "search":
            if args.batch == "-":
                urls = sys.stdin.read().strip().split("\n")
            else:
                with open(args.batch, "r") as fh:
                    urls = fh.read().strip().split("\n")
            run_batch(handler, urls, args, args)
        else:
            if args.command != "search" and not getattr(args, "url", None) and not args.batch:
                parser.parse_args([args.command, "--help"])
            handler(args, args)
    except ResearchError as exc:
        log(f"Error: {exc}")
        sys.exit(exc.code)


if __name__ == "__main__":
    main()
