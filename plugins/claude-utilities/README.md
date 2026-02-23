# claude-utilities

Useful tools that don't fit in a specific plugin.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-utilities@claudest
```

## Skills

### convert-to-markdown

Convert any webpage to clean markdown. Strips ads, navigation, popups, and cookie banners and returns just the article content. Uses [ezycopy](https://github.com/gupsammy/EzyCopy) under the hood.

Triggers on "convert this page to markdown", "extract this webpage", "save this article", "grab content from URL", "scrape this page".

**Prerequisite:** install ezycopy once before use:

```bash
curl -sSL https://raw.githubusercontent.com/gupsammy/EzyCopy/main/install.sh | sh
```

## License

MIT
