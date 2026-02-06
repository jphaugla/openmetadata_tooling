#!/bin/bash

# 1. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    echo "Make sure to export TOKEN and API_BASE (e.g., http://localhost:8585/api/v1)"
    exit 1
fi

# 2. Format URL
# This endpoint fetches all defined database services
CLEAN_URL=$(echo "${API_BASE}/services/databaseServices?include=all" | sed 's#//#/#g' | sed 's#http:/#http://#g')

echo "🔍 Fetching all defined database services..."
echo "🌐 URL: $CLEAN_URL"
echo "------------------------------------------------"

# 3. Fetch Data and Output JSON
# We use curl to get the data and pipe it to 'jq' if available for better readability
# If you don't have jq installed, it will just dump the raw string
if command -v jq >/dev/null 2>&1; then
    curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL" | jq '.'
else
    curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL"
    echo -e "\n\n💡 Pro-tip: Install 'jq' (brew install jq) to see this formatted nicely."
fi
