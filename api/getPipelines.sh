#!/bin/bash
mkdir -p "${JSON_DIR:-../json}"
SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./getPipelines.sh <service_name>"
    exit 1
fi

if [[ "$SERVICE_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$SERVICE_NAME' contains spaces. Spaces are not allowed."
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Identifying Service Type for: ${SERVICE_NAME}..."

# Try Database Service first
DB_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}")
DB_SVC_ID=$(echo "$DB_SVC_RESPONSE" | jq -r '.id')

if [ "$DB_SVC_ID" != "null" ] && [ ! -z "$DB_SVC_ID" ]; then
    SERVICE_TYPE="databaseService"
    echo "✅ Found Database Service: ${SERVICE_NAME}"
else
    # Try Search Service
    SEARCH_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/searchServices/name/${SERVICE_NAME}")
    SEARCH_SVC_ID=$(echo "$SEARCH_SVC_RESPONSE" | jq -r '.id')
    
    if [ "$SEARCH_SVC_ID" != "null" ] && [ ! -z "$SEARCH_SVC_ID" ]; then
        SERVICE_TYPE="searchService"
        echo "✅ Found Search Service: ${SERVICE_NAME}"
    else
        echo "❌ Error: Service '${SERVICE_NAME}' not found as a Database or Search service."
        exit 1
    fi
fi

echo "🔍 Searching for Ingestion Pipelines tied to: ${SERVICE_NAME} (${SERVICE_TYPE})..."

# In 1.11.4, we fetch all and use jq to filter to ensure we don't miss any due to API filter quirks
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" \
    "${BASE_URL}/services/ingestionPipelines?limit=1000&fields=owners,sourceConfig,airflowConfig")

# Check if curl failed or returned empty
if [ -z "$RESPONSE" ]; then
    echo "❌ Error: Empty response from API. Check your TOKEN and API_BASE."
    exit 1
fi

# Filter JSON to only include pipelines where the service name matches
PIPELINES=$(echo "$RESPONSE" | jq --arg svc "$SERVICE_NAME" '.data | map(select(.service.name == $svc))')
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Error processing JSON with jq."
    echo "Response Content: $RESPONSE"
    exit 1
fi

# Check if PIPELINES is null or empty
if [ -z "$PIPELINES" ] || [ "$PIPELINES" == "null" ]; then
    COUNT=0
else
    COUNT=$(echo "$PIPELINES" | jq 'length')
fi

if [ "$COUNT" -eq 0 ]; then
    echo "⚠️ No pipelines found for service: ${SERVICE_NAME}."
    echo "DEBUG: Checked $(echo "$RESPONSE" | jq '.data | length') total pipelines in the instance."
else
    echo "✅ Found $COUNT pipelines (Metadata, Usage, Profiler, etc.)."
    echo "$PIPELINES" > "${JSON_DIR:-../json}/${SERVICE_NAME}_pipelines.json"
    echo "💾 Saved to ${SERVICE_NAME}_pipelines.json"
fi
