# OpenMetadata MCP Tooling

This directory contains the Model Context Protocol (MCP) client and tooling to integrate OpenMetadata with Google Gemini. It allows the Gemini LLM to query your local OpenMetadata instance to answer questions about your data assets (tables, lineage, etc.).

## Prerequisites

### Environment Variables
The following environment variables are required. They are typically sourced from `~/.openmetadata/setEnv.sh` by the `exec.sh` script.

| Variable | Description | Example |
| :--- | :--- | :--- |
| `TOKEN` | OpenMetadata JWT/PAT for Authentication | `eyJ...` |
| `API_BASE` | OpenMetadata API Base URL | `http://localhost:8585/api/v1` |
| `GEMINI_APIKEY` | Google Gemini API Key | `AIza...` |

### System Dependencies
- **Python 3.10+** (Recommended)
- **Node.js/Npx** (Required if running server via npx, though this setup mostly connects to a running server)
- **OpenMetadata Server**: Must be running (e.g., via Docker/Minikube) at `http://localhost:8585` (or configured via variables).

## Installation

1.  **Run the install script**:
    This script creates a virtual environment `om-mcp-workspace/venv` and installs required packages (`mcp`, `google-genai`, `jupyterlab`).
    ```bash
    ./install.sh
    ```

## Usage

1.  **Start the Jupyter Environment**:
    Use the provided execution script. It handles loading the environment variables and launching Jupyter Lab.
    ```bash
    ./exec.sh
    ```

2.  **Open the Notebook**:
    Navigate to `mcp_om.ipynb` in the Jupyter interface.

3.  **Run the Cells**:
    Execute the cells to:
    -   Connect to the OpenMetadata MCP Server (Default: `http://localhost:8585/mcp`).
    -   Fetch available tools (e.g., `list_tables`, `get_table_schema`).
    -   Ask questions to Gemini (e.g., "What tables are in the movr database?").

## Code Overview: `mcp_om.ipynb`

The notebook demonstrates a manual integration of the MCP client with the Gemini Python SDK.

### Key Components

1.  **Stateless HTTP Client**:
    The OpenMetadata server uses a stateless HTTP transport for MCP (POST calls), rather than a persistent connection like SSE or stdio. We use `streamable_http_client` to handle this.
    ```python
    from mcp.client.streamable_http import streamable_http_client
    # ...
    async with streamable_http_client(url=MCP_URL, http_client=http_client) as (read, write, _):
    ```

2.  **Tool Fetching**:
    We explicitly fetch the list of available tools from the MCP server.
    ```python
    result = await session.list_tools()
    ```

3.  **Tool conversion**:
    Gemini requires tools to be defined in a specific format (`FunctionDeclaration`). We iterate through the MCP tools and convert their schema to be compatible with Gemini.

4.  **Execution Loop**:
    The standard Gemini `generate_content` call doesn't automatically execute client-side tools. The notebook implements a loop:
    -   **Send Prompt**: Ask Gemini the question, providing the available tools.
    -   **Catch Function Call**: If Gemini returns a `function_call` (e.g., `list_tables`), we pause.
    -   **Execute Tool**: We run the tool against the MCP session (`session.call_tool(...)`).
    -   **Return Result**: We feed the tool's output back to Gemini.
    -   **Repeat**: This continues until Gemini produces a final text response.
