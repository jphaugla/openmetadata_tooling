#!/bin/bash

TABLE_FQN=$1

# 1. Validate Table FQN was passed
if [ -z "$TABLE_FQN" ]; then
    echo "❌ Error: No Table FQN provided."
    echo "Usage: ./getTableMetadata.sh <table_fqn>"
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 3. Format URL and Fetch Data
# We sanitize the API_BASE to ensure no double slashes
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
# Endpoint: /api/v1/tables/name/<FQN>?fields=tags,extension
CLEAN_URL="${BASE_URL}/tables/name/${TABLE_FQN}?fields=tags,extension"

# 4. Fetch and Pretty-Print the Data
# Using -L to follow redirects if necessary
# Piping to jq for reliability and readability
curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL" | jq .
