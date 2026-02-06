#!/bin/bash

PIPELINE_NAME=$1

# 1. Validate Input
if [ -z "$PIPELINE_NAME" ]; then
    echo "Usage: ./deleteEntityPipeline.sh <PIPELINE_NAME>"
    exit 1
fi

if [[ "$PIPELINE_NAME" == *" "* ]]; then
    echo "❌ Error: Pipeline name '$PIPELINE_NAME' contains spaces."
    exit 1
fi

# 2. Validate Environment
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🗑️  Preparing to HARD DELETE pipeline entity: ${PIPELINE_NAME}"

# 3. Get the Pipeline ID
# We use FQN for standard pipelines as it's more reliable
PIPELINE_CHECK=$(curl -s -X GET "${BASE_URL}/pipelines/name/${PIPELINE_NAME}?include=all" \
  -H "Authorization: Bearer $TOKEN")

PIPELINE_ID=$(echo "$PIPELINE_CHECK" | jq -r '.id // empty')

if [ ! -z "$PIPELINE_ID" ] && [ "$PIPELINE_ID" != "null" ]; then
    echo "✅ Found ID: $PIPELINE_ID"
    
    # 4. Perform Hard Delete
    DELETE_URL="${BASE_URL}/pipelines/${PIPELINE_ID}?hardDelete=true"
    DELETE_RESPONSE=$(curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "$DELETE_URL")
    
    echo "💥 Pipeline $PIPELINE_NAME has been permanently deleted."
else
    echo "❌ Pipeline '$PIPELINE_NAME' not found. Nothing to delete."
fi
