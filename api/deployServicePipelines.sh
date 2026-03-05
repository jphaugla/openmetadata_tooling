#!/bin/bash

# Script to deploy all pipelines for a given Database or Search Service.
# This script finds all ingestion pipelines associated with the service
# and triggers their deployment to the orchestration engine.

SERVICE_NAME=$1

# 1. Validate Input
if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./deployServicePipelines.sh <service_name>"
    exit 1
fi

if [[ "$SERVICE_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$SERVICE_NAME' contains spaces. Spaces are not allowed."
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 3. Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Identifying Service for: ${SERVICE_NAME}..."

# 4. Resolve Service ID and Type
# Try Database Service first
DB_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}")
SERVICE_ID=$(echo "$DB_SVC_RESPONSE" | jq -r '.id')

if [ "$SERVICE_ID" != "null" ] && [ ! -z "$SERVICE_ID" ]; then
    SERVICE_TYPE="databaseService"
    echo "✅ Found Database Service: ${SERVICE_NAME}"
else
    # Try Search Service
    SEARCH_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/searchServices/name/${SERVICE_NAME}")
    SERVICE_ID=$(echo "$SEARCH_SVC_RESPONSE" | jq -r '.id')
    
    if [ "$SERVICE_ID" != "null" ] && [ ! -z "$SERVICE_ID" ]; then
        SERVICE_TYPE="searchService"
        echo "✅ Found Search Service: ${SERVICE_NAME}"
    else
        echo "❌ Error: Service '${SERVICE_NAME}' not found as a Database or Search service."
        exit 1
    fi
fi

echo "🔍 Searching for Ingestion Pipelines tied to: ${SERVICE_NAME}..."

# 5. Fetch and Filter Pipelines
# We fetch all pipelines and filter by service name using jq
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" \
    "${BASE_URL}/services/ingestionPipelines?limit=1000")

if [ -z "$RESPONSE" ]; then
    echo "❌ Error: Empty response from API. Check your TOKEN and API_BASE."
    exit 1
fi

PIPELINES=$(echo "$RESPONSE" | jq --arg svc "$SERVICE_NAME" '.data | map(select(.service.name == $svc))')

if [ -z "$PIPELINES" ] || [ "$PIPELINES" == "null" ] || [ "$(echo "$PIPELINES" | jq 'length')" -eq 0 ]; then
    echo "⚠️ No pipelines found for service: ${SERVICE_NAME}."
    exit 0
fi

COUNT=$(echo "$PIPELINES" | jq 'length')
echo "🚀 Found $COUNT pipelines. Starting deployment..."

# 6. Deploy Each Pipeline
echo "$PIPELINES" | jq -c '.[]' | while read -r pipeline; do
    P_NAME=$(echo "$pipeline" | jq -r '.name')
    P_ID=$(echo "$pipeline" | jq -r '.id')
    P_TYPE=$(echo "$pipeline" | jq -r '.pipelineType')
    
    
    echo "----------------------------------------------------------------"
    echo "🛰️  Deploying Pipeline: $P_NAME (ID: $P_ID)"
    
    DEPLOY_RESPONSE=$(curl -s -L -X POST "${BASE_URL}/services/ingestionPipelines/deploy/${P_ID}" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$DEPLOY_RESPONSE" | grep -q "error"; then
         echo "   ⚠️ Deploy failed for $P_NAME."
         echo "   Message: $(echo "$DEPLOY_RESPONSE" | jq -r '.message')"
    else
         echo "   ✅ Successfully Deployed!"
    fi
done

echo "----------------------------------------------------------------"
echo "🏁 Done. Processed $COUNT pipelines for ${SERVICE_NAME}."
