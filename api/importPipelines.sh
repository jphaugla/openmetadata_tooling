#!/bin/bash

# --- CONFIGURATION ---
# Set to "true" to automatically deploy/start the pipelines after import.
# Set to "false" to only create the definitions (Safe Mode).
RUN_DEPLOYMENT="false"
# ---------------------

INPUT_FILE=$1

if [ -z "$INPUT_FILE" ] || [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Usage: ./importPipelines.sh <pipelines_file.json>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$OWNER_ID" ]; then
    echo "❌ Error: Missing environment variables (TOKEN, API_BASE, or OWNER_ID)."
    exit 1
fi

# 0. Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

# 1. Resolve Owner Name and Service ID
echo "👤 Resolving name for Owner ID: $OWNER_ID..."
USER_JSON=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/users/${OWNER_ID}")
OWNER_NAME=$(echo "$USER_JSON" | jq -r '.name')

if [ "$OWNER_NAME" == "null" ] || [ -z "$OWNER_NAME" ]; then
    echo "❌ Error: Could not find user name for ID $OWNER_ID."
    exit 1
fi

SERVICE_NAME=$(basename "$INPUT_FILE" _pipelines.json)

if [[ "$SERVICE_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$SERVICE_NAME' (from filename) contains spaces. Spaces are not allowed."
    exit 1
fi

echo "🔗 Resolving Service ID for ${SERVICE_NAME}..."

# Try Database Service first
DEST_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}")
DEST_SVC_ID=$(echo "$DEST_SVC_RESPONSE" | jq -r '.id')

if [ "$DEST_SVC_ID" != "null" ] && [ ! -z "$DEST_SVC_ID" ]; then
    DEST_SVC_TYPE="databaseService"
    echo "✅ Found Database Service: ${SERVICE_NAME}"
else
    # Try Search Service
    DEST_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/searchServices/name/${SERVICE_NAME}")
    DEST_SVC_ID=$(echo "$DEST_SVC_RESPONSE" | jq -r '.id')
    
    if [ "$DEST_SVC_ID" != "null" ] && [ ! -z "$DEST_SVC_ID" ]; then
        DEST_SVC_TYPE="searchService"
        echo "✅ Found Search Service: ${SERVICE_NAME}"
    else
        echo "❌ Error: Service ${SERVICE_NAME} not found as a Database or Search service. Import the service first."
        exit 1
    fi
fi

# 2. Process Pipelines
cat "$INPUT_FILE" | jq -c '.[]' | while read -r agent; do
    NAME=$(echo "$agent" | jq -r '.name')
    P_TYPE=$(echo "$agent" | jq -r '.pipelineType')
    
    
    # Rebuild the JSON and delete the incompatible field
    CLEAN_JSON=$(echo "$agent" | jq --arg svc_id "$DEST_SVC_ID" --arg svc_type "$DEST_SVC_TYPE" --arg owner_id "$OWNER_ID" --arg owner_name "$OWNER_NAME" --arg p_type "$P_TYPE" '
    del(.sourceConfig.config.overrideLineage) | 
    {
        name: .name,
        displayName: .displayName,
        description: .description,
        pipelineType: .pipelineType,
        sourceConfig: (
            if $p_type == "metadata" then 
                (.sourceConfig | .config.ownerConfig = {
                    default: $owner_name,
                    service: $owner_name,
                    database: $owner_name,
                    enableInheritance: true
                })
            else 
                .sourceConfig 
            end
        ),
        airflowConfig: .airflowConfig,
        loggerLevel: .loggerLevel,
        service: {id: $svc_id, type: $svc_type},
        owners: [{id: $owner_id, type: "user"}]
    }')
    echo "----------------------------------------------------------------"
    echo "🚀 Step 1: Importing $P_TYPE Agent: $NAME"
    
    CREATE_RESPONSE=$(curl -s -L -X POST "${BASE_URL}/services/ingestionPipelines" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$CLEAN_JSON")
        
    PIPELINE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')

    if [ "$PIPELINE_ID" != "null" ] && [ ! -z "$PIPELINE_ID" ]; then
        echo "   ✅ Created (ID: $PIPELINE_ID)"
        
        # 🚀 Step 2: Conditional Deployment
        if [ "$RUN_DEPLOYMENT" == "true" ]; then
            echo "   sat 🛰️  Step 2: Deploying to Orchestration..."
            DEPLOY_RESPONSE=$(curl -s -L -X POST "${BASE_URL}/services/ingestionPipelines/deploy/${PIPELINE_ID}" \
                -H "Authorization: Bearer $TOKEN")
            
            # 1.11.4 Fix: Check HTTP Code or generic success, don't just rely on ID in return
            # A deploy command might just return 200 OK with the pipeline status
            if echo "$DEPLOY_RESPONSE" | grep -q "error"; then
                 echo "   ⚠️ Deploy failed."
                 echo "   Message: $(echo "$DEPLOY_RESPONSE" | jq -r '.message')"
            else
                 echo "   ✅ Successfully Deployed!"
            fi
        else
            echo "   ⏸️  Skipping Deployment (RUN_DEPLOYMENT=false). Pipeline is created but not active."
        fi
    else
        echo "   ❌ Failed to create: $(echo "$CREATE_RESPONSE" | jq -r '.message')"
    fi
done
