#!/bin/bash

SERVICE_NAME=$1
NEW_HOST_PORT=$2

# 1. Validate Input
if [ -z "$SERVICE_NAME" ] || [ -z "$NEW_HOST_PORT" ]; then
    echo "❌ Usage: ./updateDBServiceHostPort.sh <service_name> <new_host:port>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 2. Get Service ID
echo "🔍 Looking up ID for service: $SERVICE_NAME..."
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
SERVICE_ID=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}" | jq -r '.id // empty')

if [ -z "$SERVICE_ID" ] || [ "$SERVICE_ID" == "null" ]; then
    echo "❌ Error: Could not find service with name '$SERVICE_NAME'."
    exit 1
fi

echo "🆔 Found Service ID: $SERVICE_ID"

# 3. Prepare JSON Patch
# The path for hostPort is /connection/config/hostPort
PATCH_PAYLOAD=$(jq -n --arg hostport "$NEW_HOST_PORT" '[{
    "op": "replace",
    "path": "/connection/config/hostPort",
    "value": $hostport
}]')

# 4. Execute PATCH
echo "📡 Sending PATCH request to update hostPort to: $NEW_HOST_PORT..."

RESPONSE=$(curl -s -L -X PATCH "${BASE_URL}/services/databaseServices/${SERVICE_ID}" \
    -H "Content-Type: application/json-patch+json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$PATCH_PAYLOAD")

# 5. Handle Response
UPDATED_PORT=$(echo "$RESPONSE" | jq -r '.connection.config.hostPort // empty')

if [ "$UPDATED_PORT" == "$NEW_HOST_PORT" ]; then
    echo "✅ Successfully updated hostPort for '$SERVICE_NAME' to: $UPDATED_PORT"
else
    echo "❌ Failed to update service."
    echo "💬 Server Response: $RESPONSE"
    exit 1
fi
