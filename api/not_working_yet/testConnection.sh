#!/bin/bash
SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./testConnection.sh <service_name>"
    exit 1
fi

BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Fetching current config for ${SERVICE_NAME}..."
# 1. Get the service definition
SERVICE_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}")

# 2. Extract connection and serviceType 
CONNECTION=$(echo "$SERVICE_JSON" | jq '.connection')
SVC_TYPE=$(echo "$SERVICE_JSON" | jq -r '.serviceType')

# 3. Construct the 'TestConnectionRequest' payload required by 1.11.4
# Note: The endpoint is /services/testConnection (Generic), NOT /services/databaseServices/...
PAYLOAD=$(jq -n \
  --argjson conn "$CONNECTION" \
  --arg svcType "$SVC_TYPE" \
  '{connection: {config: $conn}, serviceType: $svcType, connectionType: "Database"}')

echo "📡 Triggering UI-style Test Connection..."
RESPONSE=$(curl -s -X POST "${BASE_URL}/services/testConnection" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$PAYLOAD")

# 4. Parse the step-by-step results
echo "------------------------------------------"
if echo "$RESPONSE" | jq -e '.steps' > /dev/null; then
    echo "$RESPONSE" | jq -r '.steps[] | "Step: \(.name) \nStatus: \(.status) \nMessage: \(.message) \n---"'
else
    echo "❌ API Error Response:"
    echo "$RESPONSE" | jq '.'
fi
