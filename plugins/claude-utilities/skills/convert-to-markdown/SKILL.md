---
name: convert-to-markdown
description: >
  This skill should be used when the user asks to "convert this page to markdown",
  "extract this webpage", "save this article", "grab content from URL", "get markdown
  from this link", "scrape this page", provides a URL to extract, or wants clean web
  content without ads and clutter.
argument-hint: "<URL>"
allowed-tools:
  - Bash(ezycopy:*)
  - Bash(curl:*)
  - AskUserQuestion
---

# Web-to-Markdown via EzyCopy

Extract clean markdown from any URL using the `ezycopy` CLI.

## Phase 1: Determine Extraction Mode

Default mode uses fast HTTP fetch. Add `--browser` when the page relies on client-side
JavaScript to render its content or when authentication cookies are required — the default
fetcher only sees the raw HTML response, not the JS-rendered DOM.

Common `--browser` cases: Twitter/X, single-page applications, paywalled content.

### Flags

- `-c` — copy output to clipboard
- `-o <path>` — save to file or directory
- `--browser` — use headless Chrome for JS-rendered or authenticated pages
- `--no-images` — strip image links
- `-t <duration>` — timeout (default: 30s)

## Phase 2: Execute

Run `ezycopy <URL> [flags]` with the chosen mode.

In `--browser` mode: run as a foreground process and do not redirect stderr with `2>&1`.
Chrome outputs diagnostic messages to stderr that should flow naturally rather than
polluting stdout capture.

## Phase 3: Handle Failure

If the output is empty or suspiciously short and `--browser` was not used, retry with
`--browser` — the site likely requires JS rendering.

If `ezycopy` is not found, ask the user before installing:

```
curl -sSL https://raw.githubusercontent.com/gupsammy/EzyCopy/main/install.sh | sh
```

## Phase 4: Deliver

Present the extracted markdown to the user. If the user requested a file save, use `-o`.
If they requested clipboard, use `-c`. When no explicit destination was given, display the
content directly.
