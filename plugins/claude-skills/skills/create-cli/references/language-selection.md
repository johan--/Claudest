# Language Selection for CLI Tools

## Default: Go

Single binary, fast startup, no runtime dependency on target machine, strong stdlib, mature
CLI ecosystem (`cobra`, `flag`). Start here unless a push factor applies.

## Push Factors (when to deviate)

| Condition | Use instead |
|-----------|-------------|
| Key library only exists in Python (data, ML, media processing) | Python |
| Embedding into an existing Python codebase | Python |
| CLI wraps a JS/TS library directly, or must distribute via npm | TypeScript/Node |
| Embedding into an existing JS/TS codebase | TypeScript/Node |
| Startup latency < 10ms or memory footprint is critical | Rust |
| Simple glue script (< ~80 lines), CI-only, or max Unix portability | Bash |
| Team has no Go experience and the CLI is short-lived | Match team language |

## Parser Quick Reference

| Language | Parser | Notes |
|----------|--------|-------|
| Go | `cobra` | subcommands; `flag` stdlib for simple flags-only tools |
| Python | `argparse` | stdlib, no dep; `click` for decorator-style; `typer` for type-annotated |
| TypeScript/Node | `yargs` | batteries-included; `commander` for lightweight |
| Rust | `clap` | derive macros; full-featured |
| Bash | `getopts` | POSIX built-in; `argbash` for complex flag parsing |

## Distribution Model

**Single binary** — one compiled file, no runtime needed on target machine. User downloads
and runs it directly. Native to Go and Rust.

**Runtime-dependent** — requires an interpreter (Python, Node.js, JVM) installed first, then
package installation. Native to Python, TypeScript/Node, Java.

**Bundled binary** — interpreter + code packed into one file by a tool (PyInstaller, pkg,
deno compile). Produces a large binary (50–150 MB) vs native binaries (5–15 MB). Works, but
has edge cases with native extensions.

### When to prioritize single binary
- Target users are non-developers, or machine state is unknown (CI, remote servers)
- Public distribution — "download and run" is the expected UX
- Container size matters (Go binary: ~10 MB; Python image with deps: 200+ MB)
- Must work reliably across diverse OS/arch combinations

### When runtime dependency is acceptable
- All target users already have the runtime (data scientists → Python; web devs → Node)
- Critical libraries only exist in that ecosystem (media processing, ML, etc.)
- Internal tools in a controlled environment where the runtime is mandated
- Development speed outweighs distribution polish

## Distribution Quick Reference

| Language | Model | Default distribution |
|----------|-------|----------------------|
| Go | Single binary | compiled binary; `goreleaser` for cross-platform CI |
| Rust | Single binary | compiled binary; `cargo install` or GitHub Releases |
| Python | Runtime-dependent | `pip install` / `pipx install`; `pyinstaller` for bundled |
| TypeScript/Node | Runtime-dependent | `npm install -g` / `npx`; `pkg` / `esbuild` for bundled |
| Bash | Script | single `.sh` file; no build step |
