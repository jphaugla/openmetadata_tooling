#!/bin/bash
# Sources environment variables from ~/.collate/setEnv.sh
# and follows the validation pattern of scripts in the api/ directory.

# 1. Source Environment Variables
if [ -f ~/.collate/setEnv.sh ]; then
    source ~/.collate/setEnv.sh
else
    echo "❌ Error: ~/.collate/setEnv.sh not found."
    exit 1
fi

# 2. Map GEMINI_APIKEY to GEMINI_API_KEY for the CLI
if [ ! -z "$GEMINI_APIKEY" ]; then
    export GEMINI_API_KEY="$GEMINI_APIKEY"
fi

# 3. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 4. Derive MCP URL from API_BASE
# Example: https://your-openmetadata-url.com/api/v1 -> https://your-openmetadata-url.com/mcp
BASE_URL=$(echo "${API_BASE}" | sed 's#/api/v1##' | sed 's#/$##')
MCP_URL="${BASE_URL}/mcp"

echo "🔍 OpenMetadata Instance: ${BASE_URL}"
echo "🚀 Adding OpenMetadata MCP server via Gemini CLI..."

# Ensure .gemini directory exists to prevent ENOENT errors
mkdir -p ~/.gemini

# 5. Execute the Gemini MCP registration
gemini mcp add -t stdio OpenMetadata \
  npx -y mcp-remote "${MCP_URL}" \
  --auth-server-url="${MCP_URL}" \
  --client-id="OpenMetadata" \
  --verbose \
  --clean \
  --header "Authorization: Bearer ${TOKEN}" \
  -e AUTH_HEADER="Bearer ${TOKEN}"
