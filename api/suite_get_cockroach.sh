#!/bin/bash

# Validate environment variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting CockroachDB Suite Export..."
echo "------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "Processing Service: $SERVICE_NAME"
    
    # Export Service Definition
    ./getDBService.sh "$SERVICE_NAME"
    
    # Export Pipelines
    ./getPipelines.sh "$SERVICE_NAME"
    
    echo "------------------------------------------"
done

echo "✅ Suite export complete."
