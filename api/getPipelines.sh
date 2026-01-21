#!/bin/bash
SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./getPipelines.sh <service_name>"
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Searching for Ingestion Pipelines tied to: ${SERVICE_NAME}..."

# In 1.11.4, we fetch all and use jq to filter to ensure we don't miss any due to API filter quirks
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" \
    "${BASE_URL}/services/ingestionPipelines?limit=1000&fields=owners,sourceConfig,airflowConfig")

# Filter JSON to only include pipelines where the service name matches
PIPELINES=$(echo "$RESPONSE" | jq --arg svc "$SERVICE_NAME" '.data | map(select(.service.name == $svc))')
COUNT=$(echo "$PIPELINES" | jq 'length')

if [ "$COUNT" -eq 0 ]; then
    echo "⚠️ No pipelines found for service: ${SERVICE_NAME}."
    echo "DEBUG: Checked $(echo "$RESPONSE" | jq '.data | length') total pipelines in the instance."
else
    echo "✅ Found $COUNT pipelines (Metadata, Usage, Profiler, etc.)."
    echo "$PIPELINES" > "${SERVICE_NAME}_pipelines.json"
    echo "💾 Saved to ${SERVICE_NAME}_pipelines.json"
fi
