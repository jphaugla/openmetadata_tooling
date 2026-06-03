#!/bin/bash

# Ensure required environment variables are set
if [ -z "$API_BASE" ] || [ -z "$TOKEN" ]; then
  echo "Error: API_BASE and/or TOKEN environment variables are not set."
  echo "Please ensure they are exported in your current shell before running this script."
  exit 1
fi

BASE_URL=$(echo "${API_BASE}" | sed 's#/api/v1##' | sed 's#/$##')

CONFIG_DIR="${HOME}/Library/Application Support/Claude"
CONFIG_FILE="${CONFIG_DIR}/claude_desktop_config.json"

mkdir -p "$CONFIG_DIR"

cat << EOF > "$CONFIG_FILE"
{
  "mcpServers": {
    "Collate": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "${BASE_URL}/mcp",
        "--auth-server-url=${BASE_URL}/mcp",
        "--client-id=Collate",
        "--verbose", "--clean",
        "--header", "Authorization: Bearer ${TOKEN}"
      ]
    }
  }
}
EOF

echo "Successfully updated Claude Desktop configuration at $CONFIG_FILE"
echo "Targeting: $BASE_URL"
echo "Please restart Claude Desktop for the changes to take effect."
