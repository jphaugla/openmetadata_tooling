#!/bin/bash
INPUT_FILE=$1

if [ -z "$INPUT_FILE" ] || [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Usage: ./importPipelines.sh <pipelines_file.json>"
    exit 1
fi

# 1. Get the NEW Service ID from the destination
# This is required because pipelines are 'owned' by a service ID
SERVICE_NAME=$(basename "$INPUT_FILE" _pipelines.json)
echo "🔗 Looking up Destination ID for Service: $SERVICE_NAME"

SERVICE_INFO=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/services/databaseServices/name/${SERVICE_NAME}")
DEST_SERVICE_ID=$(echo "$SERVICE_INFO" | jq -r '.id')

if [ "$DEST_SERVICE_ID" == "null" ]; then
    echo "❌ Error: Could not find Service '$SERVICE_NAME' on destination. Import the service first!"
    exit 1
fi

echo "✅ Destination Service ID found: $DEST_SERVICE_ID"

# 2. Iterate and Import
cat "$INPUT_FILE" | jq -c '.[]' | while read -r pipeline; do
    P_NAME=$(echo "$pipeline" | jq -r '.name')
    
    # We rebuild the JSON for 1.11.4: 
    # We must replace the old service ID with the new one
    CLEAN_JSON=$(echo "$pipeline" | jq --arg svc_id "$DEST_SERVICE_ID" --arg owner_id "$OWNER_ID" '{
        name: .name,
        displayName: .displayName,
        description: .description,
        pipelineType: .pipelineType,
        sourceConfig: .sourceConfig,
        airflowConfig: .airflowConfig,
        loggerLevel: .loggerLevel,
        service: {
            id: $svc_id,
            type: "databaseService"
        },
        owners: [{id: $owner_id, type: "user"}]
    }')

    echo "🚀 Importing Pipeline: $P_NAME..."
    
    curl -s -X POST "${API_BASE}/services/ingestionPipelines" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$CLEAN_JSON" | jq -r '"Result: " + .name + " (ID: " + .id + ")"'
done
