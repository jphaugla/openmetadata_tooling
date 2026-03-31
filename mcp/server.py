import os
import asyncio
import httpx
from mcp import ClientSession
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Tool, TextContent, ImageContent

# Variables - defaults from common usage or environment
OM_PAT = os.getenv("TOKEN") or os.getenv("OPENMETADATA_AUTH_TOKEN")
API_BASE = os.getenv("API_BASE") # e.g. http://localhost:8585/api/v1

# Derive MCP URL from API_BASE if not provided
if "MCP_URL" in os.environ:
    MCP_URL = os.environ["MCP_URL"]
elif API_BASE:
    # Most common case: strip /api/v1 and add /mcp
    if "/api/v1" in API_BASE:
        MCP_URL = API_BASE.split("/api/v1")[0] + "/mcp"
    else:
        MCP_URL = API_BASE.rstrip("/") + "/mcp"
else:
    MCP_URL = "http://localhost:8585/mcp"

TIMEOUT = httpx.Timeout(90, read=None)

# Initialize the Server
server = Server("OpenMetadata MCP Bridge")

async def get_http_session(http_client):
    """Creates an MCP client session over HTTP."""
    # Note: streamable_http_client returns a context manager (read, write, _)
    transport = streamable_http_client(url=MCP_URL, http_client=http_client)
    async with transport as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Lists available tools by proxying to the OpenMetadata instance."""
    try:
        headers = {"Authorization": f"Bearer {OM_PAT}"} if OM_PAT else {}
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as http_client:
            async with streamable_http_client(url=MCP_URL, http_client=http_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return result.tools
    except Exception as e:
        print(f"Error listing tools from {MCP_URL}: {e}", file=os.sys.stderr)
        return []

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent]:
    """Calls a tool by proxying to the OpenMetadata instance."""
    try:
        headers = {"Authorization": f"Bearer {OM_PAT}"} if OM_PAT else {}
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as http_client:
            async with streamable_http_client(url=MCP_URL, http_client=http_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(name, arguments=arguments)
                    return result.content
    except Exception as e:
        print(f"Error calling tool {name} from {MCP_URL}: {e}", file=os.sys.stderr)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Runs the server over stdio."""
    print(f"OpenMetadata MCP Bridge starting, proxying to {MCP_URL}...", file=os.sys.stderr)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
