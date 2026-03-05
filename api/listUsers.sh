#!/bin/bash

# 1. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    echo "Make sure to export TOKEN and API_BASE (e.g., http://localhost:8585/api/v1)"
    exit 1
fi

# 2. Format URL
# Ensure we don't have double slashes
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
USER_URL="${BASE_URL}/users?limit=100"

echo "🔍 Fetching users list..."
echo "------------------------------------------------"

# 3. Fetch and format
RESPONSE_FILE=$(mktemp)
HTTP_CODE=$(curl -s -L -w "%{http_code}" -o "$RESPONSE_FILE" -H "Authorization: Bearer $TOKEN" "$USER_URL")

if [ "$HTTP_CODE" -eq 200 ]; then
    if command -v jq >/dev/null 2>&1; then
        jq -r '.data[] | "Name: \(.name)\nDisplay: \(.displayName // "N/A")\nID: \(.id)\nAdmin: \(.isAdmin)\nBot: \(.isBot)\n---"' "$RESPONSE_FILE"
    else
        cat "$RESPONSE_FILE"
    fi
elif [ "$HTTP_CODE" -eq 401 ]; then
    echo "❌ Error: 401 Unauthorized. Your TOKEN is likely expired or invalid for this 1.12.1 installation."
    echo "💡 Try logging into the UI and generating a new token."
else
    echo "❌ Error: API request failed with HTTP $HTTP_CODE"
    cat "$RESPONSE_FILE"
fi

rm -f "$RESPONSE_FILE"
