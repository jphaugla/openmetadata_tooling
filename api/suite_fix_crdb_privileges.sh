#!/bin/bash

# Ensure required environment variables are set
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting Privilege Fix for CockroachDB Suite..."
echo "🛠️  Adding allow_unsafe_internals=true to connection options..."
echo "--------------------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    
    if [ -f "./patchCRDBConnectionOptions.sh" ]; then
        ./patchCRDBConnectionOptions.sh "$SERVICE_NAME"
    else
        echo "❌ Error: patchCRDBConnectionOptions.sh not found."
        exit 1
    fi
    
    echo "--------------------------------------------------------"
done

echo "✅ All existing services patched."
