#!/bin/bash

INPUT_FILE=$1

# 1. Validate Input and Environment
if [ -z "$INPUT_FILE" ] || [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: Please provide a valid JSON file."
    echo "Usage: ./database_service_import.sh <exported_service.json>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$OWNER_ID" ]; then
    echo "❌ Error: Missing environment variables (TOKEN, API_BASE, or OWNER_ID)."
    exit 1
fi

# Ensure jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ Error: 'jq' is required but not installed."
    exit 1
fi

echo "🚀 Importing service from: $INPUT_FILE"
echo "👤 Assigning Owner ID: $OWNER_ID"

# 2. Clean the JSON and Inject the NEW Owner
# We use jq to rebuild the object:
# - Taking name, serviceType, description, and connection from the file
# - Manually creating the owners array using the $OWNER_ID variable
CLEAN_JSON=$(jq --arg owner_id "$OWNER_ID" '{
    name: .name,
    serviceType: .serviceType,
    description: .description,
    connection: .connection,
    owners: [
        {
            id: $owner_id,
            type: "user"
        }
    ]
}' "$INPUT_FILE")

# 3. Execute the Import
echo "📡 Sending POST request to $API_BASE..."

RESPONSE=$(curl -s -X POST "$API_BASE/services/databaseServices" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$CLEAN_JSON")

# 4. Handle the Response
NEW_ID=$(echo "$RESPONSE" | jq -r '.id // empty')

if [ ! -z "$NEW_ID" ] && [ "$NEW_ID" != "null" ]; then
    echo "✅ Service successfully imported!"
    echo "🆔 New Service ID: $NEW_ID"
    echo "🔗 Service Name: $(echo "$RESPONSE" | jq -r '.name')"
else
    echo "❌ Failed to import service."
    echo "💬 Server Response: $RESPONSE"
    exit 1
fi
