# OpenMetadata MCP Tooling

This directory contains all tooling to integrate **OpenMetadata** with AI clients using the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It supports three clients:

| Client | Method | Transport |
| :--- | :--- | :--- |
| **Gemini CLI** | `gemini_cli.sh` via `mcp-remote` (Node) | stdio → HTTP |
| **Claude Desktop** | `server.py` Python bridge | stdio → HTTP |
| **Antigravity** | `server.py` Python bridge | stdio → HTTP |

All clients ultimately connect to the same OpenMetadata MCP HTTP endpoint, using your token from `~/.collate/setEnv.sh`.

---

## Prerequisites

### Environment Variables
Set in `~/.collate/setEnv.sh` and sourced automatically by `gemini_cli.sh`:

| Variable | Description |
| :--- | :--- |
| `TOKEN` | OpenMetadata JWT/PAT for Authentication |
| `API_BASE` | OpenMetadata API Base URL (e.g. `https://your-openmetadata-url.com/api/v1`) |
| `GEMINI_APIKEY` | Google Gemini API Key (for Gemini CLI) |

### System Dependencies
- **Node.js / npx** — required for Gemini CLI setup (`mcp-remote`)
- **Python 3.10+** — required for the Python bridge (`server.py`)

---

## Setup

### For Gemini CLI (uses `mcp-remote`)

No separate install needed — `npx` handles it automatically. Just run:

```bash
chmod +x gemini_cli.sh
./gemini_cli.sh
```

This script:
1. Sources your environment from `~/.collate/setEnv.sh`
2. Derives the MCP URL from `$API_BASE`
3. Registers the OpenMetadata server in `~/.gemini/settings.json`

Verify the connection:
```bash
gemini mcp list
# ✓ OpenMetadata: ... (stdio) - Connected
```

### For Claude Desktop & Antigravity (uses `server.py`)

Run the setup script once to create the Python virtual environment:

```bash
chmod +x setup.sh
./setup.sh
```

This creates `venv/` in this directory and installs `mcp` and `httpx`.

---

## Client Configuration

### Gemini CLI

Managed automatically by `gemini_cli.sh`. Settings are stored in `~/.gemini/settings.json`.

The MCP server entry looks like this (auto-generated):
```json
{
  "mcpServers": {
    "OpenMetadata": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "https://your-openmetadata-url.com/mcp",
        "--auth-server-url=https://your-openmetadata-url.com/mcp",
        "--client-id=OpenMetadata",
        "--verbose", "--clean",
        "--header", "Authorization: Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### Claude Desktop

#### Method 1: Official Collate PAT via `mcp-remote` (Recommended)
This method follows the [official Collate documentation](https://docs.getcollate.io/collate-ai/mcp/claude#connect-with-personal-access-token-pat) using the `npx` bridge. We have provided a helper script to automatically generate the `claude_desktop_config.json` file using your current environment variables.

Ensure that the required environment variables (`API_BASE` and `TOKEN`) are set in your terminal session, and then run the script to update your configuration:

```bash
# Ensure API_BASE and TOKEN are exported in your environment
./switch_claude.sh
```
Restart Claude Desktop after running this command to apply the new configuration.

#### Method 2: Python Bridge (`server.py`)
Alternatively, if you prefer the local Python bridge, add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openmetadata-mcp-bridge": {
      "command": "<path-to-your-repo>/mcp/venv/bin/python3",
      "args": [
        "<path-to-your-repo>/mcp/server.py"
      ],
      "env": {
        "TOKEN": "YOUR_TOKEN_HERE",
        "API_BASE": "https://your-openmetadata-url.com/api/v1"
      }
    }
  }
}
```

Restart Claude Desktop after updating the config.

### Antigravity

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "openmetadata-mcp-bridge": {
      "command": "<path-to-your-repo>/mcp/venv/bin/python3",
      "args": [
        "<path-to-your-repo>/mcp/server.py"
      ],
      "env": {
        "TOKEN": "YOUR_TOKEN_HERE",
        "API_BASE": "https://your-openmetadata-url.com/api/v1"
      }
    }
  }
}
```

---

## File Reference

| File | Purpose |
| :--- | :--- |
| `gemini_cli.sh` | Registers the MCP server with the Gemini CLI using `mcp-remote` |
| `server.py` | Python bridge — proxies stdio MCP ↔ OpenMetadata HTTP endpoint |
| `setup.sh` | Creates `venv/` and installs Python dependencies for `server.py` |
| `mcp_om.ipynb` | Jupyter notebook demonstrating manual MCP + Gemini Python SDK integration |
| `install.sh` | Sets up the Jupyter environment in `om-mcp-workspace/` |
| `exec.sh` | Launches Jupyter Lab with environment variables loaded |

---

## How the Python Bridge Works (`server.py`)

OpenMetadata uses a stateless HTTP transport for MCP (POST calls), but clients like Claude Desktop and Antigravity expect a `stdio` JSON-RPC interface. `server.py` bridges this gap:

- **Receives**: `stdio` JSON-RPC messages from the client
- **Forwards**: Requests to the OpenMetadata MCP HTTP endpoint with Bearer auth
- **Returns**: Tool lists and results back over `stdio`

```python
# Key pattern used in server.py
async with streamable_http_client(url=MCP_URL, http_client=http_client) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.list_tools()
```
