# OpenClaw Ecosystem Patterns

OpenClaw-specific patterns that skill authors need to know when generating skills for the
pi-coding-agent / OpenClaw ecosystem. These patterns have no equivalent in Claude Code and
represent conventions unique to OpenClaw's architecture.

---

## 1. Documentation Research

Use `clawdocs` CLI to look up OpenClaw's own documentation from within generated skill bodies:

```bash
# Fetch a specific documentation page (no header, quiet mode)
clawdocs get "tools/skills" --no-header -q

# Search for relevant pages by slug
clawdocs search "frontmatter" --slugs-only

# Fetch a topic page
clawdocs fetch "concepts/system-prompt" --no-header -q
```

Common useful slugs: `tools/skills`, `concepts/system-prompt`, `tools/exec`, `tools/sessions`,
`config/gateway`, `tools/groups`.

Generated skills that need to reference live OpenClaw config or query capabilities should
use `clawdocs` rather than hardcoding documentation that may drift.

---

## 2. Sub-Agent Delegation

OpenClaw uses `sessions_spawn` for background delegation. This is the equivalent of Claude
Code's `Task(subagent_type=...)`, with key differences:

- `sessions_spawn` is **non-blocking** — it launches the sub-agent and the result is
  announced back to chat when complete (the main agent continues without waiting)
- **No `subagent_type`** — all sub-agents are general purpose; there are no specialized
  agent types to route to
- Sub-agents receive only `AGENTS.md` + `TOOLS.md` in their system prompt — they do not
  inherit the current agent's skills, persona context, or conversation history
- Sub-agents can read skill files via the `read` tool if you reference the skill path

When to use `sessions_spawn` vs inline execution:
- Use inline for steps that must complete before the next step starts
- Use `sessions_spawn` for parallel work, long-running operations, or steps whose results
  are independently useful without blocking the main workflow

---

## 3. Cross-Skill References

There is no `Skill` tool in OpenClaw — the model cannot programmatically invoke another
skill. Skills are triggered by the routing model when the user's message matches the
description. To reference another skill from within a generated skill body:

**Option A — Tell the model to read the skill:**
```markdown
Read `{baseDir}/../<other-skill-name>/SKILL.md` via the `read` tool to access its instructions.
```

**Option B — Tell the user to invoke it:**
```markdown
Instruct the user to type `/<other-skill-name>` to trigger the [other skill] workflow.
```

**Option C — Copy the relevant instructions inline** — for small, stable sub-procedures
that shouldn't require the user to switch workflows.

Fully qualified skill references are not needed in OpenClaw (there is no plugin namespace
to qualify against in frontmatter); just reference by skill name.

---

## 4. Tool Groups

OpenClaw organizes tools into groups. When writing skill bodies that reference tools,
use the correct OpenClaw tool names (not Claude Code tool names):

| Group | Tools | Purpose |
|-------|-------|---------|
| `group:fs` | `read`, `write`, `edit`, `apply_patch` | File system operations |
| `group:runtime` | `exec` (primary), `bash`, `process` | Shell / subprocess execution |
| `group:web` | `web_search`, `web_fetch` | Web access |
| `group:sessions` | `sessions_spawn`, `sessions_list`, `sessions_get` | Sub-agent delegation |

**Key translation table** (Claude Code → OpenClaw):

| Claude Code | OpenClaw |
|-------------|----------|
| `Bash` | `exec` |
| `Read` | `read` |
| `Write` | `write` |
| `Edit` | `edit` |
| `Glob` | use `exec` + `find`/`ls` |
| `Grep` | use `exec` + `grep`/`rg` |
| `WebSearch` | `web_search` |
| `WebFetch` | `web_fetch` |
| `Task(subagent_type=...)` | `sessions_spawn` |
| `AskUserQuestion` | agent asks conversationally (no dedicated tool) |
| `Skill` | agent reads SKILL.md via `read` tool |
| `EnterPlanMode` / `ExitPlanMode` | not available |
| `NotebookEdit` | not available |

---

## 5. Installation Guidance

When a generated skill is ready, the user can install it in one of two places:

**Workspace skill** (affects only this workspace, next session):
```bash
cp -r <skill-directory> <workspace>/skills/<skill-name>/
```
The workspace path is whatever directory is configured in `agents.defaults.workspace`
in the user's `openclaw.json`.

**Managed skill** (shared across all agents and workspaces on this machine):
```bash
cp -r <skill-directory> ~/.openclaw/skills/<skill-name>/
```

**Distribution via ClawHub:**
```bash
clawhub publish <skill-directory> --slug <slug> --version 1.0.0 --tags latest
```

Skills take effect on the **next new session** after installation — the current session
was snapshotted at startup and won't pick up new skills until a fresh session begins.

---

## 6. Path Conventions

| Purpose | Pattern | Notes |
|---------|---------|-------|
| Skill-relative files | `{baseDir}/references/file.md` | Substituted at load time |
| Scripts in skill | `{baseDir}/scripts/script.py` | Called via `exec` tool |
| Managed skills | `~/.openclaw/skills/<name>/` | Shared across all agents |
| Workspace skills | `<workspace>/skills/<name>/` | Per-workspace, configured via `openclaw.json` |
| Other skill in same collection | `{baseDir}/../<other-skill>/SKILL.md` | Relative path via `read` |

`{baseDir}` is substituted *before the model sees the skill body* — it becomes the absolute
path to the skill's directory. This substitution is performed by the pi-coding-agent skill
loader, not by the shell. Do not use shell variable syntax (`$baseDir`).
