# retro

A Claude Code plugin for structured error and success logging in agentic coding workflows.

The core loop: log what went wrong (and right), trace it back to **your** input, and improve over time. Patterns compound into permanent CLAUDE.md guardrails that make the agent smarter alongside you.

## Install

```
/plugin marketplace add rubin-johnson/retro
/plugin install retro@rubin-johnson
```

Restart Claude Code to load the plugin.

## Commands

### `/retro:error [optional description]`

Structured interview to log an agentic coding error. Traces the error back to your prompt, context, or harness setup. After logging, prompts you to rewind the conversation to clean stale debugging context.

### `/retro:success [optional description]`

Log what worked and why. Successes are rarer than errors so they're weighted more heavily -- 2 successes in a category get promoted to a CLAUDE.md rule.

### `/retro:review [optional filter]`

Review your log to surface patterns:
- Top failure modes and trends
- Milestone detection (errors in a category followed by successes = leveling up)
- Auto-generated CLAUDE.md rules from repeated patterns
- Option to write rules directly into your project CLAUDE.md

## How It Works

**Error taxonomy** covers four categories:
- **prompt** -- ambiguous instructions, missing constraints, wrong abstraction level
- **context** -- context rot, stale context, missing context
- **harness** -- wrong agent type, no guardrails, bad parallelization
- **meta** -- rushed to implementation, didn't ask clarifying questions

**Success taxonomy** mirrors these categories, tracking what worked.

**Pattern detection** triggers at:
- 3+ errors in a category -> generates a CLAUDE.md prevention rule
- 2+ successes in a category -> promotes the technique to a CLAUDE.md rule

**Session reminders** -- a lightweight hook checks if you have 5+ unreviewed entries and nudges you to run `/retro:review`.

## Data

Entries are stored in `~/.retro/retro.db` (SQLite). Override with the `RETRO_DB` environment variable.

No external dependencies. No MCP server. Just Python stdlib and SQLite.

## Development

```bash
git clone https://github.com/rubin-johnson/retro.git
cd retro
uv sync
uv run pytest tests/ -v
```

For local plugin testing:
```
/plugin marketplace add ~/path/to/retro
/plugin install retro@retro-dev
```

## License

MIT
