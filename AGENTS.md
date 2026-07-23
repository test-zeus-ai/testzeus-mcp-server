# AGENTS.md — testzeus-mcp-server

Guidance for AI coding agents working in this repository. Provider-agnostic:
any agent (Claude Code, Cursor, etc.) should read this before making changes.

## What this project is

`testzeus-mcp-server` is a FastMCP server that exposes TestZeus SDK
functionality to MCP clients (Claude Desktop, Cursor, and other MCP hosts). It
wraps `testzeus-sdk` and surfaces its capabilities as MCP tools. The console
entry point is `testzeus-mcp-server` (`testzeus_mcp_server.__main__:main`).

## Build, test, and lint

Uses **uv** (not Poetry). Python **>=3.11,<4.0**.

```bash
make dev-install   # uv sync --dev
make fmt           # uv run ruff format (testzeus_mcp_server/, tests/)
make lint          # uv run ruff check --fix
make test          # ruff + uv run pytest (--maxfail=1)
make run           # uv run testzeus-mcp-server
```

- Formatter/linter is **ruff**, line length **100** (not 200 like the SDK/CLI).
  CI runs `ruff check` + `ruff format --check` as blocking gates; `pytest` is
  non-blocking. Run `make fmt` before committing.
- Keep the `testzeus-sdk` dependency floor high enough that a stale SDK missing
  a needed capability can't satisfy the install.

## Architecture

- `testzeus_mcp_server/` — the server package. Tools are registered on the
  FastMCP server; each tool prepares a TestZeus client, calls the SDK, and
  returns a JSON-serializable result.
- Tools mirror SDK capabilities. When adding tools for a new SDK area, follow an
  existing group (e.g. the agent-harness / `*_adversary_*` tools) as the
  template, and keep long return payloads within the 100-char line limit
  (extract `payload = json.dumps(...)` into a variable rather than inlining).

## Conventions

- Match surrounding code style and comment density.
- Never commit secrets or hardcode credentials.
- Line length is **100** here — do not copy the SDK/CLI's 200.
- Releases follow the `Makefile` release targets; keep versions unique.
- `main` is protected: all changes land via pull request.
