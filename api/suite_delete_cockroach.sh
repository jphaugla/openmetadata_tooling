#!/bin/bash

# Ensure toolbox scripts exist
if [ ! -f "./delete_service.sh" ] || [ ! -f "./deletePipelines.sh" ]; then
    echo "❌ Error: ./delete_service.sh or ./deletePipelines.sh not found."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🧹 Starting CockroachDB Suite Cleanup..."
echo "------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    
    # 1. Delete Pipelines First (Clean slate)
    ./deletePipelines.sh "$SERVICE_NAME"
    
    # 2. Delete the Service
    ./delete_service.sh "$SERVICE_NAME"
    
    echo "------------------------------------------"
done

echo "✅ Suite cleanup complete."
