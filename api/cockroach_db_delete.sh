#!/bin/bash

# Validate environment variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "Error: TOKEN or API_BASE environment variables are not set."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    if [[ "$SERVICE_NAME" == *" "* ]]; then
        echo "❌ Error: Service name '$SERVICE_NAME' contains spaces. Spaces are not allowed."
        continue
    fi
    PIPELINE_NAME="${SERVICE_NAME}_metadata"
    
    echo "------------------------------------------"
    echo "Cleaning up: $SERVICE_NAME"

    # 1. Delete the Ingestion Pipeline first (Targeting the FQN)
    # FQN is usually ServiceName.PipelineName
    PIPELINE_FQN="${SERVICE_NAME}.${PIPELINE_NAME}"
    curl -s -X DELETE "$API_BASE/ingestionPipelines/name/$PIPELINE_FQN?hardDelete=true" \
    -H "Authorization: Bearer $TOKEN" > /dev/null

    # 2. Get the Service ID using 'include=all' to find soft-deleted zombies
    # Added -L to follow redirects and removed any potential double slashes
    CLEAN_URL=$(echo "${API_BASE}/services/databaseServices/name/${SERVICE_NAME}?include=all" | sed 's#//#/#g' | sed 's#http:/#http://#g')
    
    RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL")
    SERVICE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | grep -o '[^"]*$' | head -n 1)

    if [ ! -z "$SERVICE_ID" ]; then
        # 3. Perform the Hard Delete using the UUID
        DELETE_URL=$(echo "${API_BASE}/services/databaseServices/$SERVICE_ID?hardDelete=true&recursive=true" | sed 's#//#/#g' | sed 's#http:/#http://#g')
        
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$DELETE_URL" -H "Authorization: Bearer $TOKEN")
        echo "🗑️ Hard deleted $SERVICE_NAME (ID: $SERVICE_ID) - Status: $STATUS"
    else
        echo "❓ $SERVICE_NAME not found via API. Checking if it appears in list..."
        # Fallback: List all and find the ID manually if name lookup fails
        FALLBACK_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/services/databaseServices" | grep -B 1 "\"name\":\"$SERVICE_NAME\"" | grep -o '"id":"[^"]*' | grep -o '[^"]*$')
        
        if [ ! -z "$FALLBACK_ID" ]; then
             curl -s -X DELETE "$API_BASE/services/databaseServices/$FALLBACK_ID?hardDelete=true&recursive=true" -H "Authorization: Bearer $TOKEN"
             echo "🗑️ Found and deleted via fallback: $FALLBACK_ID"
        else
             echo "❌ Really could not find $SERVICE_NAME."
        fi
    fi
done
