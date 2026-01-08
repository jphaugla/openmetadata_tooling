#!/bin/bash

SERVICE_NAME=$1

# 1. Validate Input
if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: ./delete_service.sh <SERVICE_NAME>"
    exit 1
fi

# 2. Validate Environment
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

echo "🗑️  Preparing to HARD DELETE service: ${SERVICE_NAME}"

# 3. Get the Service ID first
CLEAN_URL=$(echo "${API_BASE}/services/databaseServices/name/${SERVICE_NAME}" | sed 's#//#/#g' | sed 's#http:/#http://#g')
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$CLEAN_URL")
SERVICE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | grep -o '[^"]*$' | head -1)

if [ ! -z "$SERVICE_ID" ]; then
    echo "✅ Found ID: $SERVICE_ID"
    # 4. Perform Hard Delete (recursive removes child databases/tables)
    DELETE_URL="${API_BASE}/services/databaseServices/${SERVICE_ID}?hardDelete=true&recursive=true"
    DELETE_RESPONSE=$(curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "$DELETE_URL")
    
    echo "💥 Service $SERVICE_NAME has been permanently deleted."
else
    echo "❓ $SERVICE_NAME not found. Checking fallback list..."
    FALLBACK_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/services/databaseServices" | grep -B 1 "\"name\":\"$SERVICE_NAME\"" | grep -o '"id":"[^"]*' | grep -o '[^"]*$' | head -1)
    
    if [ ! -z "$FALLBACK_ID" ]; then
        curl -s -X DELETE -H "Authorization: Bearer $TOKEN" "${API_BASE}/services/databaseServices/${FALLBACK_ID}?hardDelete=true&recursive=true"
        echo "💥 Found and deleted via fallback: $FALLBACK_ID"
    else
        echo "❌ Service not found. Nothing to delete."
    fi
fi
