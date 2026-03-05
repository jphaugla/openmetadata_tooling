#!/bin/bash

SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./patchCRDBConnectionOptions.sh <service_name>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

# 1. Get Service ID
echo "🔍 Looking up ID for service: $SERVICE_NAME..."
SERVICE_ID=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}" | jq -r '.id // empty')

if [ -z "$SERVICE_ID" ] || [ "$SERVICE_ID" == "null" ]; then
    echo "❌ Error: Could not find service with name '$SERVICE_NAME'."
    exit 1
fi

# 2. Prepare JSON Patch to fix the connection options
# We remove the invalid direct key and add the correct 'options' parameter
PATCH_PAYLOAD=$(jq -n '[
    {
        "op": "remove",
        "path": "/connection/config/connectionOptions/allow_unsafe_internals"
    },
    {
        "op": "add",
        "path": "/connection/config/connectionOptions/options",
        "value": "-callow_unsafe_internals=true"
    }
]' 2>/dev/null || jq -n '[
    {
        "op": "add",
        "path": "/connection/config/connectionOptions/options",
        "value": "-callow_unsafe_internals=true"
    }
]')

echo "📡 Patching service '$SERVICE_NAME' (ID: $SERVICE_ID) with allow_unsafe_internals=true..."

RESPONSE=$(curl -s -L -X PATCH "${BASE_URL}/services/databaseServices/${SERVICE_ID}" \
    -H "Content-Type: application/json-patch+json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$PATCH_PAYLOAD")

# 3. Verify
RESULT=$(echo "$RESPONSE" | jq -r '.connection.config.connectionOptions.options // empty')

if [ "$RESULT" == "-callow_unsafe_internals=true" ]; then
    echo "✅ Successfully patched $SERVICE_NAME"
else
    echo "❌ Failed to patch service."
    echo "💬 Server Response: $RESPONSE"
    exit 1
fi
