#!/bin/bash
# Install dependencies for the OpenMetadata MCP bridge
python3 -m venv venv
source venv/bin/activate
pip install mcp httpx
echo "Setup complete. You can now use the bridge."
