# Foorilla MCP Server

An MCP (Model Context Protocol) server that exposes the [Foorilla](https://foorilla.com) job market API as tools callable by Claude — in both Claude Code and Claude Desktop.

## What is Foorilla

Foorilla is a job market data platform providing programmatic access to job listings, company profiles, salary benchmarks, and topic/skill taxonomies. Data is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

- API base: `https://foorilla.com/api/v1/`
- Docs: `https://foorilla.com/api/v1/docs`
- Schema: `https://foorilla.com/api/v1/schema.json`
- Current API version: 1.1.2

Rate limits: 600 requests/minute, 5 requests/second.

## Available Tools

| Tool | Description |
|---|---|
| `search_jobs` | Search job listings filtered by country, topic, tag, and date range |
| `get_job` | Get full details for a single job by Foorilla ID |
| `search_salaries` | Get salary benchmarks filtered by country and topic |
| `list_topics` | Browse the skill/technology taxonomy to find topic IDs |
| `list_countries` | List countries with their ISO codes (used for `search_jobs` filters) |
| `get_company` | Get company profile by Foorilla company ID |
| `list_companies` | List all companies active on Foorilla (paginated) |

Country codes are resolved to Foorilla IDs internally — pass standard ISO-2 codes (e.g. `"CH"`, `"DE"`) directly to `search_jobs` and `search_salaries`.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- A Foorilla API key (obtain from your account at foorilla.com)

## Setup

### 1. Clone or locate the project

```
/Users/dd/PycharmProjects/foorilla_mcp_server/
```

### 2. Install dependencies

```bash
cd /Users/dd/PycharmProjects/foorilla_mcp_server
uv sync
```

This creates `.venv/` with `mcp` and `httpx` installed.

### 3. Register in Claude Code (user scope)

```bash
claude mcp add --scope user foorilla \
  -e FOORILLA_API_KEY=YOUR_API_KEY \
  -- /Users/dd/PycharmProjects/foorilla_mcp_server/.venv/bin/python \
     /Users/dd/PycharmProjects/foorilla_mcp_server/server.py
```

This writes to `~/.claude.json` and applies to all Claude Code sessions.

### 4. Register in Claude Desktop

Add the following block inside `"mcpServers"` in `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
"foorilla": {
  "command": "/Users/dd/PycharmProjects/foorilla_mcp_server/.venv/bin/python",
  "args": [
    "/Users/dd/PycharmProjects/foorilla_mcp_server/server.py"
  ],
  "env": {
    "FOORILLA_API_KEY": "YOUR_API_KEY"
  }
}
```

Restart Claude Desktop after editing the config.

### 5. Verify the server starts

```bash
FOORILLA_API_KEY=YOUR_API_KEY \
  .venv/bin/python -c "import server; print('OK')"
```

## Usage

Once registered, Claude can call the tools directly. Example prompts:

**Job search in Switzerland:**
> "Search Foorilla for AI Engineer jobs in Switzerland published after 2026-01-01"

Claude will call `list_topics` to resolve relevant topic IDs, then `search_jobs` with `country_codes=["CH"]`.

**Salary benchmarks:**
> "What are the salary ranges for Python Data Engineers in Switzerland on Foorilla?"

Claude will call `search_salaries` with `country_codes=["CH"]` and appropriate topic IDs.

**Company research:**
> "Get details about the company that posted Foorilla job ID 12345"

Claude will call `get_job` to retrieve the company ID, then `get_company` for the full profile.

**Topic exploration:**
> "List all Foorilla topics related to LangChain or LangGraph"

Claude will call `list_topics` with a search filter.

## Project Structure

```
foorilla_mcp_server/
├── server.py        # MCP server — all tools defined here
├── pyproject.toml   # uv project config and dependencies
├── uv.lock          # locked dependency versions
└── README.md        # this file
```

## API Key

The server reads the key from the `FOORILLA_API_KEY` environment variable. It raises a `RuntimeError` at request time if the variable is not set — no silent failures.

Keep the key out of source control. It is injected via the MCP server config (`env` block) in both Claude Code and Claude Desktop registrations.
