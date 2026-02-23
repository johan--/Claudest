# Example CLI Spec: `snapr`

A complete worked example covering all deliverable sections, including agent-aware patterns:
TTY auto-detection, NDJSON list output, structured errors with executable hints, and compound
output. Use as a reference for output format and level of detail.

---

## 1. Name

`snapr`

## 2. One-liner

Take and restore filesystem snapshots.

## 3. USAGE

```
snapr [global flags] <subcommand> [args]

snapr snapshot <path> [--name <name>] [--tag <tag>]
snapr restore  <snapshot-id> <target-path> [--force] [--dry-run]
snapr list     [--tag <tag>]
snapr delete   <snapshot-id> [--force]
```

## 4. Subcommands

| Subcommand | Description | Idempotent? |
|-----------|-------------|-------------|
| `snapshot <path>` | Capture a versioned archive of `<path>`. Returns snapshot ID + metadata. | Creates a new snapshot each time |
| `restore <id> <target>` | Restore snapshot to `<target>`. Fails if target non-empty without `--force`. | No — overwrites data |
| `list` | List all snapshots; filter by tag. | Yes |
| `delete <id>` | Delete a snapshot. Prompts for confirmation unless `--force`. | No |

## 5. Global flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-h, --help` | bool | — | Show help; ignore all other args |
| `--version` | bool | — | Print version to stdout, exit 0 |
| `-q, --quiet` | bool | false | Suppress progress output; errors still go to stderr |
| `-v, --verbose` | bool | false | Emit debug output to stderr |
| `--human` | bool | false | Force human-readable output even when piped |
| `--no-color` | bool | false | Disable ANSI color; also respected via `NO_COLOR` env var |
| `--config <path>` | string | `~/.snapr/config.toml` | Path to config file |

Subcommand-specific flags:

| Flag | Applies to | Description |
|------|-----------|-------------|
| `--name <name>` | `snapshot` | Human label; defaults to ISO8601 timestamp |
| `--tag <tag>` | `snapshot`, `list` | Group/filter snapshots |
| `--dry-run` | `restore` | Show what would be overwritten without writing |
| `--force` | `restore`, `delete` | Skip confirmation; required for non-interactive use |

## 6. I/O contract

**Output mode (TTY auto-detection):** When stdout is a TTY, emit human-readable colored
output. When stdout is piped or non-TTY (always the case for agent callers), emit structured
JSON automatically — no flag required. `--human` forces human output; `--json` is accepted
as an alias for non-TTY mode.

**stdout:** Snapshot objects, list output (NDJSON in non-TTY — one JSON object per line),
version string. `snapshot` always returns the created snapshot's ID and metadata fields on
stdout, even in quiet mode, so callers don't need a follow-up `list` call.

**stderr:** Progress messages, verbose debug, warnings. In non-TTY mode, errors are emitted
as a structured JSON object (see §7). Never mixes with stdout.

**stdin:** `restore` accepts `-` as `<target>` to pipe restored content to stdout
(single-file snapshots only).

## 7. Exit codes and error format

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Runtime error (snapshot not found, I/O failure, permission denied) |
| `2` | Invalid usage (unknown flag, missing required arg, bad type) |
| `3` | Target conflict — restore target is non-empty and `--force` not passed |

**Non-TTY error object** (emitted on stderr):
```json
{"error": "not_found", "message": "Snapshot 'abc123' does not exist.", "hint": "snapr list --json"}
```

The three fields are always present: `error` (snake_case machine code), `message` (one
human-readable sentence), `hint` (exact CLI invocation the caller can run to recover,
or `null` if no recovery action applies).

## 8. Env/config

**Environment variables:**

| Variable | Overrides | Notes |
|----------|-----------|-------|
| `SNAPR_DIR` | default snapshot dir (`~/.snapr/snapshots/`) | Set in CI to a shared volume |
| `SNAPR_CONFIG` | `--config` flag | Lower precedence than the flag |
| `NO_COLOR` | `--no-color` | Standard; respected automatically |

**Config file** (`~/.snapr/config.toml`; project-local `.snapr.toml` in CWD also checked):

```toml
snapshot_dir   = "~/.snapr/snapshots"
default_tag    = ""
retention_days = 30
```

**Precedence (high → low):** flags > env vars > project config (`.snapr.toml`) > user
config (`~/.snapr/config.toml`) > built-in defaults.

## 9. Examples

```bash
# Create a snapshot — stdout returns full object; agent can read ID without a follow-up call
snapr snapshot ./src --name "before-refactor" --tag "dev"
# non-TTY output: {"id":"abc123","name":"before-refactor","tag":"dev","path":"./src","created_at":"2026-02-23T14:00:00Z"}

# List all snapshots — NDJSON in non-TTY mode, one object per line; pipeable without buffering
snapr list --tag "dev" | jq -r '.id'
# abc123
# def456

# Restore non-interactively in CI — --force skips confirmation; exit code signals outcome
snapr restore abc123 ./src --force --quiet
# exit 0 on success; exit 3 if target non-empty (agent checks exit code, not stderr)

# Preview a restore — dry-run + non-TTY shows JSON diff of what would change
snapr restore abc123 ./src --dry-run

# Agent error recovery pattern — hint field contains the exact next command to run
snapr restore xyz999 ./src --force
# stderr: {"error":"not_found","message":"Snapshot 'xyz999' does not exist.","hint":"snapr list --json"}
```
