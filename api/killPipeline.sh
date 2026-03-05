#!/bin/bash

# Script to kill a running or queued ingestion pipeline.
# This is useful when a job is stuck and blocking other runs.

PIPELINE_NAME=$1

# 1. Validate Input
if [ -z "$PIPELINE_NAME" ]; then
    echo "❌ Usage: ./killPipeline.sh <pipeline_name_or_fqn>"
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 3. Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Finding Pipeline ID for: ${PIPELINE_NAME}..."

# 4. Resolve Pipeline ID
# We look it up by name/FQN
# Note: FQN lookup is usually more reliable
P_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/ingestionPipelines/name/${PIPELINE_NAME}")
P_ID=$(echo "$P_RESPONSE" | jq -r '.id // empty')

if [ -z "$P_ID" ] || [ "$P_ID" == "null" ]; then
    echo "❓ Not found by name. Searching via list..."
    P_ID=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/ingestionPipelines?limit=1000" | \
           jq -r --arg name "$PIPELINE_NAME" '.data[] | select(.name == $name or .fullyQualifiedName == $name) | .id' | head -n 1)
fi

if [ -z "$P_ID" ]; then
    echo "❌ Error: Could not find pipeline '${PIPELINE_NAME}'."
    exit 1
fi

echo "🎯 Found Pipeline ID: $P_ID"
echo "💀 Sending KILL signal..."

# 5. Send Kill Request
KILL_RESPONSE=$(curl -s -L -X POST "${BASE_URL}/services/ingestionPipelines/kill/${P_ID}" \
     -H "Authorization: Bearer $TOKEN")

if echo "$KILL_RESPONSE" | grep -q "error"; then
    echo "⚠️  Kill operation reported a problem."
    echo "   Message: $(echo "$KILL_RESPONSE" | jq -r '.message // "Unknown error")"
else
    echo "✅ Kill signal sent successfully. It may take a few moments for the status to update in the UI."
fi
