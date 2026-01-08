#!/bin/bash

SERVICE_NAME=$1

# 1. Validate Service Name was passed
if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Error: No Service Name provided."
    echo "Usage: ./checkService.sh <service_name>"
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

echo "🔍 Checking for Service: ${SERVICE_NAME}..."

# 3. Format URL and Fetch Data
# We include 'testConnectionResult' in the fields to get the actual status
CLEAN_URL=$(echo "${API_BASE}/services/databaseServices/name/${SERVICE_NAME}?fields=testConnectionResult&include=all" | sed 's#//#/#g' | sed 's#http:/#http://#g')
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL")

# 4. Extract ID and Connection Status
SERVICE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | grep -o '[^"]*$' | head -1)

# Extract status from testConnectionResult object
# Values are usually "Successful" or "Failed"
STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*' | grep -o '[^"]*$' | head -1)

if [ ! -z "$SERVICE_ID" ]; then
    # If status is empty, it means the connection hasn't been tested yet
    [ -z "$STATUS" ] && STATUS="Unknown (Not Tested)"
    
    echo "✅ Found ${SERVICE_NAME}"
    echo "🆔 ID: $SERVICE_ID"
    echo "📡 Status: $STATUS"
else
    echo "❓ $SERVICE_NAME not found via direct name lookup. Checking fallback list..."
    
    # Fallback: Search the full list (useful if there are URL encoding issues)
    FALLBACK_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/services/databaseServices" | grep -B 1 "\"name\":\"$SERVICE_NAME\"" | grep -o '"id":"[^"]*' | grep -o '[^"]*$' | head -1)

    if [ ! -z "$FALLBACK_ID" ]; then
        echo "⚠️ Found via fallback! ID: $FALLBACK_ID"
    else
        echo "❌ Really could not find $SERVICE_NAME."
    fi
fi
