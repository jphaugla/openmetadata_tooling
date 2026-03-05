#!/bin/bash

# Script to deploy all pipelines for the CockroachDB suite.
# This iterates through the standard Cockroach services and triggers
# deployment for their associated ingestion pipelines.

# 1. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# 2. Ensure supporting script exists
if [ ! -f "./deployServicePipelines.sh" ]; then
    echo "❌ Error: deployServicePipelines.sh not found in the current directory."
    exit 1
fi

# 3. Define the suite of databases
databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting Pipeline Deployment for CockroachDB Suite..."
echo "--------------------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "📦 Service: $SERVICE_NAME"
    
    # Trigger deployment for all pipelines tied to this service
    ./deployServicePipelines.sh "$SERVICE_NAME"
    
    echo "--------------------------------------------------------"
done

echo "✅ All CockroachDB suite pipelines processed."
