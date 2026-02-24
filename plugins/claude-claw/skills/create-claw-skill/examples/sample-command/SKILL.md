---
name: fetch-page
description: Fetch and summarize a web page
argument-hint: <url>
user-invocable: true
---

# Fetch Page

Fetch the content of a URL and produce a concise summary.

## Process

1. Fetch the URL passed as `$1` using the `web_fetch` tool
2. Summarize the main content in 3–5 sentences, preserving key facts and figures
3. List any notable links or resources mentioned in the page
4. If the URL is inaccessible, report the error and suggest checking the URL format
