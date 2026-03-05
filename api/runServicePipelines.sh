#!/bin/bash

# Script to trigger and orchestrate ingestion pipelines for a service.
# It runs the Metadata pipeline first and waits for it to succeed
# before triggering all other associated pipelines.

SERVICE_NAME=$1

# 1. Validate Input
if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./runServicePipelines.sh <service_name>"
    exit 1
fi

if [[ "$SERVICE_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$SERVICE_NAME' contains spaces."
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 3. Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Locating pipelines for Service: ${SERVICE_NAME}..."

# 4. Fetch All Pipelines for the Service
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" \
    "${BASE_URL}/services/ingestionPipelines?limit=1000")

if [ -z "$RESPONSE" ] || [ "$RESPONSE" == "null" ]; then
    echo "❌ Error: Could not fetch pipelines."
    exit 1
fi

PIPELINES=$(echo "$RESPONSE" | jq --arg svc "$SERVICE_NAME" '.data | map(select(.service.name == $svc))')

if [ -z "$PIPELINES" ] || [ "$PIPELINES" == "null" ] || [ "$(echo "$PIPELINES" | jq 'length')" -eq 0 ]; then
    echo "⚠️ No pipelines found for service: ${SERVICE_NAME}."
    exit 0
fi

# 5. Identify Metadata vs Other Pipelines
METADATA_PIPELINE=$(echo "$PIPELINES" | jq -c '.[] | select(.pipelineType == "metadata")')
OTHER_PIPELINES=$(echo "$PIPELINES" | jq -c '.[] | select(.pipelineType != "metadata")')

if [ -z "$METADATA_PIPELINE" ]; then
    echo "❌ Error: No Metadata pipeline found for ${SERVICE_NAME}. Metadata is required first."
    exit 1
fi

M_ID=$(echo "$METADATA_PIPELINE" | jq -r '.id')
M_NAME=$(echo "$METADATA_PIPELINE" | jq -r '.name')

# 6. Trigger Metadata Pipeline
echo "🚀 Step 1: Triggering Metadata Pipeline: $M_NAME (ID: $M_ID)..."
TRIGGER_RESPONSE=$(curl -s -L -X POST "${BASE_URL}/services/ingestionPipelines/trigger/${M_ID}" \
    -H "Authorization: Bearer $TOKEN")

if echo "$TRIGGER_RESPONSE" | grep -q "error"; then
    echo "❌ Failed to trigger Metadata pipeline: $(echo "$TRIGGER_RESPONSE" | jq -r '.message')"
    exit 1
fi

# 7. Polling for Completion
echo "⏳ Waiting for Metadata Pipeline to complete (check every 15s)..."
MAX_RETRIES=80 # 20 minutes total
RETRY_COUNT=0
STATUS="running"

while [[ "$STATUS" == "running" || "$STATUS" == "queued" || "$STATUS" == "null" ]]; do
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Timeout: Metadata pipeline did not complete within 20 minutes."
        exit 1
    fi

    sleep 15
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # Fetch latest status from the main pipeline record
    # This is often more immediate than the /status history endpoint
    STATUS_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/services/ingestionPipelines/${M_ID}?fields=pipelineStatuses")
    
    # Check if we got a valid response
    if [ -z "$STATUS_RESPONSE" ] || [ "$STATUS_RESPONSE" == "null" ]; then
        STATUS="running"
    else
        # Extract status from the pipelineStatuses object
        # Note: OpenMetadata returns pipelineState for the latest run here
        STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.pipelineStatuses.pipelineState // "running"' | tr '[:upper:]' '[:lower:]')
        LATEST_RUN=$(echo "$STATUS_RESPONSE" | jq -c '.pipelineStatuses // empty')
    fi
    
    echo "   [Attempt $RETRY_COUNT] Current Status: $STATUS"
    
    if [ "$STATUS" == "success" ]; then
        echo "✅ Metadata Pipeline Completed Successfully!"
        break
    elif [ "$STATUS" == "failed" ] || [ "$STATUS" == "partialsuccess" ]; then
        echo "❌ Metadata Pipeline ended with state: $STATUS. Aborting subsequent pipelines."
        # If it failed, show the error log if available in the status response
        ERROR_MSG=$(echo "$LATEST_RUN" | jq -r '.error // empty')
        [ -n "$ERROR_MSG" ] && echo "   Error Detail: $ERROR_MSG"
        exit 1
    elif [ "$STATUS" != "running" ] && [ "$STATUS" != "queued" ] && [ "$STATUS" != "null" ]; then
        # This handles unexpected states like 'stopped' or 'aborted'
        echo "⚠️  Metadata Pipeline ended with unexpected state: $STATUS. Aborting."
        exit 1
    fi
    
    # Debug: If stuck for more than 8 attempts (2 mins), show the raw JSON status record once
    if [ $RETRY_COUNT -eq 8 ]; then
        echo "   🔍 Debugging: Raw status of latest run: $LATEST_RUN"
    fi
done

# 8. Trigger Other Pipelines
if [ -z "$OTHER_PIPELINES" ]; then
    echo "ℹ️ No other pipelines found. Process complete."
    exit 0
fi

echo "🚀 Step 2: Triggering dependent pipelines..."
echo "$OTHER_PIPELINES" | while read -r p; do
    P_ID=$(echo "$p" | jq -r '.id')
    P_NAME=$(echo "$p" | jq -r '.name')
    P_TYPE=$(echo "$p" | jq -r '.pipelineType')

    
    echo "   🛰️  Triggering $P_TYPE: $P_NAME..."
    TRIGGER_DEP=$(curl -s -L -X POST "${BASE_URL}/services/ingestionPipelines/trigger/${P_ID}" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$TRIGGER_DEP" | grep -q "error"; then
        echo "      ❌ Failed: $(echo "$TRIGGER_DEP" | jq -r '.message // "Unknown error"')"
    else
        echo "      ✅ Triggered successfully."
    fi
done

echo "🏁 All pipelines for ${SERVICE_NAME} have been triggered successfully."
