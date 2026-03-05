#!/bin/bash

# Ensure toolbox scripts exist
if [ ! -f "./delete_service.sh" ] || [ ! -f "./deletePipelines.sh" ]; then
    echo "❌ Error: ./delete_service.sh or ./deletePipelines.sh not found."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

DELETE_COUNT=0

echo "🧹 Starting CockroachDB Suite Cleanup..."
echo "------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    
    # 1. Delete Pipelines First (Clean slate)
    ./deletePipelines.sh "$SERVICE_NAME"
    
    # 2. Delete the Service
    # Capture output to check if it was actually deleted
    OUTPUT=$(./delete_service.sh "$SERVICE_NAME")
    echo "$OUTPUT"
    
    if echo "$OUTPUT" | grep -iq "deleted"; then
        ((DELETE_COUNT++))
    fi
    
    echo "------------------------------------------"
done

echo "TOTAL_DELETED=$DELETE_COUNT"
echo "✅ Suite cleanup complete."
