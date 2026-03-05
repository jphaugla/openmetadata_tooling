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

# 2. Clean the JSON and Inject the NEW Owner
# Sanitize API_BASE to handle trailing slashes
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🚀 Importing service from: $INPUT_FILE"
echo "👤 Assigning Owner ID: $OWNER_ID"

# We use envsubst to allow environment variables in the JSON file
# then use jq to rebuild the object:
# - Taking name, serviceType, description, and connection from the file
# - Manually creating the owners array using the $OWNER_ID variable
TEMPORARY_JSON=$(envsubst < "$INPUT_FILE")
CLEAN_JSON=$(echo "$TEMPORARY_JSON" | jq -c --arg owner_id "$OWNER_ID" '
    # Logic to inject CockroachDB session variables if needed
    if .serviceType == "Cockroach" then
        .connection.config.connectionOptions += {"options": "-callow_unsafe_internals=true"}
    else
        .
    end |
    {
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
    }
')

# Validate that we got a valid JSON with required fields
IMPORT_NAME=$(echo "$CLEAN_JSON" | jq -r '.name // empty')
IMPORT_TYPE=$(echo "$CLEAN_JSON" | jq -r '.serviceType // empty')

if [ -z "$IMPORT_NAME" ] || [ "$IMPORT_NAME" == "null" ] || [ -z "$IMPORT_TYPE" ] || [ "$IMPORT_TYPE" == "null" ]; then
    echo "❌ Error: Could not extract 'name' or 'serviceType' from $INPUT_FILE."
    echo "Please check if the JSON file is valid and contains these fields."
    exit 1
fi

if [[ "$IMPORT_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$IMPORT_NAME' (from JSON) contains spaces. Spaces are not allowed."
    exit 1
fi

# 3. Execute the Import
echo "📡 Sending POST request to $BASE_URL..."

RESPONSE=$(curl -s -L -X POST "${BASE_URL}/services/databaseServices" \
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
