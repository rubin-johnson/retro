# AGENTS.md

Agent-agnostic retro logging with MCP server.

## Test Command

```bash
uv run python -m pytest
```

Use `uv run python -m pytest`, not `uv run pytest`. The `-m` invocation injects the cwd into `sys.path`, making the `retro` package importable even before a full editable install.

## Architecture

- `retro/db.py` — SQLite operations, schema migrations; stdlib only; canonical source for the plugin cache copy at `~/.claude/plugins/cache/retro-dev/retro/0.1.0/scripts/db.py`
- `retro/mcp_server.py` — FastMCP server exposing log_error, log_success, query, stats
- `scripts/db.py` — thin shim that imports and calls `retro.db.main()`

## Schema

Current schema version: 2. Migration from v1 → v2 adds `agent TEXT` column automatically.

## Plugin Sync

The Claude plugin uses `scripts/db.py` directly. After changes to `retro/db.py`, sync with:

```bash
cp retro/db.py ~/.claude/plugins/cache/retro-dev/retro/0.1.0/scripts/db.py
```

## Agent Identity

`agent` field on entries is populated from:
1. `agent` key in the JSON payload (explicit, e.g. Gemini via MCP tool parameter)
2. `RETRO_AGENT` env var fallback (Claude sets `RETRO_AGENT=claude`, Codex sets `RETRO_AGENT=codex`)
