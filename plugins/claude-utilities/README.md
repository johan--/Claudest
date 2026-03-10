# claude-utilities ![v0.2.1](https://img.shields.io/badge/v0.2.1-blue?style=flat-square)

Useful tools that don't fit in a specific plugin.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-utilities@claudest
```

## Skills

### convert-to-markdown

Convert any webpage to clean markdown. Strips ads, navigation, popups, and cookie banners and returns just the article content. Uses [ezycopy](https://github.com/gupsammy/EzyCopy) under the hood.

Triggers on: "convert this page to markdown", "extract this webpage", "save this article", "grab content from URL", "get markdown from this link", "scrape this page", or when you paste a URL and ask for clean content.

**Extraction modes**

The default mode uses a fast HTTP fetch and works for most static pages. For pages that rely on client-side JavaScript to render their content — or that require authentication cookies — pass `--browser` to use headless Chrome instead.

Common `--browser` cases: Twitter/X, single-page applications, paywalled content.

**Flags**

| Flag | Description |
|------|-------------|
| `--browser` | Use headless Chrome for JS-rendered or authenticated pages |
| `-o <path>` | Save output to a file or directory |
| `-c` | Copy output to clipboard |
| `--no-images` | Strip image links from output |
| `-t <duration>` | Set a fetch timeout (default: 30s) |

**Prerequisite:** install ezycopy once before use:

```bash
curl -sSL https://raw.githubusercontent.com/gupsammy/EzyCopy/main/install.sh | sh
```

## License

MIT
