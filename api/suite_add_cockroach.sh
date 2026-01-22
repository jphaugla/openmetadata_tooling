#!/bin/bash

# Validate environment variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$OWNER_ID" ]; then
    echo "❌ Error: Missing environment variables (TOKEN, API_BASE, or OWNER_ID)."
    exit 1
fi

# Ensure toolbox scripts exist
if [ ! -f "./importDBService.sh" ] || [ ! -f "./importPipelines.sh" ] || [ ! -f "./suite_delete_cockroach.sh" ]; then
    echo "❌ Error: Required toolbox scripts not found."
    exit 1
fi

echo "🧹 Running Pre-import Cleanup..."
./suite_delete_cockroach.sh

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting CockroachDB Suite Import..."
echo "------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "Processing Service: $SERVICE_NAME"
    
    # Import Service Definition
    if [ -f "${SERVICE_NAME}.json" ]; then
        ./importDBService.sh "${SERVICE_NAME}.json"
    else
        echo "⚠️  Warning: ${SERVICE_NAME}.json not found. Skipping service import."
    fi

    # Import Pipelines
    if [ -f "${SERVICE_NAME}_pipelines.json" ]; then
        ./importPipelines.sh "${SERVICE_NAME}_pipelines.json"
    else
        echo "⚠️  Warning: ${SERVICE_NAME}_pipelines.json not found. Skipping pipeline import."
    fi
    
    echo "------------------------------------------"
done

echo "✅ Suite import complete."
