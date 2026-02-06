#!/bin/bash

SERVICE_NAME=$1

# 1. Validate Input
if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: ./deletePipelineService.sh <SERVICE_NAME>"
    exit 1
fi

if [[ "$SERVICE_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$SERVICE_NAME' contains spaces. Spaces are not allowed."
    exit 1
fi

# 2. Validate Environment
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🗑️  Preparing to HARD DELETE pipeline service: ${SERVICE_NAME}"

# 3. Get the Service ID first
SERVICE_CHECK=$(curl -s -X GET "${BASE_URL}/services/pipelineServices/name/${SERVICE_NAME}" \
  -H "Authorization: Bearer $TOKEN")

SERVICE_ID=$(echo "$SERVICE_CHECK" | jq -r '.id // empty')

if [ ! -z "$SERVICE_ID" ] && [ "$SERVICE_ID" != "null" ]; then
    echo "✅ Found ID: $SERVICE_ID"
    # 4. Perform Hard Delete (recursive removes child pipelines)
    DELETE_URL="${BASE_URL}/services/pipelineServices/${SERVICE_ID}?hardDelete=true&recursive=true"
    DELETE_RESPONSE=$(curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "$DELETE_URL")
    
    echo "💥 Pipeline Service $SERVICE_NAME and its pipelines have been permanently deleted."
else
    echo "❌ Pipeline Service '$SERVICE_NAME' not found. Nothing to delete."
fi
