#!/bin/bash

# Script to run all pipelines for the CockroachDB suite.
# This iterates through the standard Cockroach services and triggers
# runServicePipelines.sh for each, which handles metadata-first orchestration.

# 1. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 2. Ensure supporting script exists
if [ ! -f "./runServicePipelines.sh" ]; then
    echo "❌ Error: runServicePipelines.sh not found in the current directory."
    exit 1
fi

# 3. Define the suite of databases
databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting Full Pipeline Execution for CockroachDB Suite..."
echo "--------------------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "📦 Service: $SERVICE_NAME"
    
    # Trigger and wait for completion for this specific service
    # runServicePipelines.sh handles the Metadata-first orchestration
    ./runServicePipelines.sh "$SERVICE_NAME"
    
    echo "--------------------------------------------------------"
done

echo "✅ All CockroachDB suite pipelines have been successfully executed."
