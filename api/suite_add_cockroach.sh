#!/bin/bash
mkdir -p "${JSON_DIR:-../json}/databaseService"
mkdir -p "${JSON_DIR:-../json}/pipelines"

# Validate environment variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$OWNER_ID" ]; then
    echo "❌ Error: Missing environment variables (TOKEN, API_BASE, or OWNER_ID)."
    exit 1
fi

# 👤 Validate OWNER_ID and get name
echo "🔍 Validating Owner ID: ${OWNER_ID}..."
CLEAN_BASE=$(echo "${API_BASE}" | sed 's#/$##')
OWNER_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${CLEAN_BASE}/users/${OWNER_ID}")

# Attempt to extract name from user response
OWNER_NAME=$(echo "$OWNER_RESPONSE" | grep -o '"name":"[^"]*' | head -n 1 | cut -d'"' -f4)

# Fallback to team check if user not found
if [ -z "$OWNER_NAME" ]; then
    OWNER_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${CLEAN_BASE}/teams/${OWNER_ID}")
    OWNER_NAME=$(echo "$OWNER_RESPONSE" | grep -o '"name":"[^"]*' | head -n 1 | cut -d'"' -f4)
    TYPE="Team"
else
    TYPE="User"
fi

if [ -z "$OWNER_NAME" ]; then
    echo "❌ Error: Invalid OWNER_ID. Could not find User or Team with ID ${OWNER_ID} in $API_BASE."
    exit 1
fi

echo "✅ Validated $TYPE: ${OWNER_NAME}"

# Ensure toolbox scripts exist
if [ ! -f "./importDBService.sh" ] || [ ! -f "./importPipelines.sh" ] || [ ! -f "./suite_delete_cockroach.sh" ]; then
    echo "❌ Error: Required toolbox scripts not found."
    exit 1
fi

echo "🧹 Running Pre-import Cleanup..."
# Capture output to parse the deletion count
CLEANUP_OUTPUT=$(./suite_delete_cockroach.sh)
echo "$CLEANUP_OUTPUT"
DELETE_COUNT=$(echo "$CLEANUP_OUTPUT" | grep "TOTAL_DELETED" | cut -d'=' -f2)

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting CockroachDB Suite Import..."
echo "------------------------------------------"

if [ "${DELETE_COUNT:-0}" -gt 0 ]; then
    echo "Pause for 30 seconds to make sure all the deletes are synced..."
    # Pause for 30 seconds
    sleep 30
    echo "30 seconds have passed. Continuing with the script."
else
    echo "No services were deleted. Skipping 30 second sync wait."
fi

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "Processing Service: $SERVICE_NAME"
    
    # Import Service Definition
    if [ -f "${JSON_DIR:-../json}/databaseService/${SERVICE_NAME}.json" ]; then
        ./importDBService.sh "${JSON_DIR:-../json}/databaseService/${SERVICE_NAME}.json"
    else
        echo "⚠️  Warning: ${SERVICE_NAME}.json not found. Skipping service import."
    fi

    # Import Pipelines
    if [ -f "${JSON_DIR:-../json}/pipelines/${SERVICE_NAME}_pipelines.json" ]; then
        ./importPipelines.sh "${JSON_DIR:-../json}/pipelines/${SERVICE_NAME}_pipelines.json"
    else
        echo "⚠️  Warning: ${SERVICE_NAME}_pipelines.json not found. Skipping pipeline import."
    fi
    
    echo "------------------------------------------"
done

echo "✅ Suite import complete."
