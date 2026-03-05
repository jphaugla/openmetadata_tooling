#!/bin/bash

NEW_HOST_PORT=$1

# 1. Validate Input
if [ -z "$NEW_HOST_PORT" ]; then
    echo "❌ Usage: ./suite_update_host_port_cockroach.sh <new_host:port>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# Ensure the update tool exists
if [ ! -f "./updateDBServiceHostPort.sh" ]; then
    echo "❌ Error: updateDBServiceHostPort.sh not found."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

echo "🚀 Starting CockroachDB Suite Host/Port Update..."
echo "📡 Target Host/Port: $NEW_HOST_PORT"
echo "------------------------------------------"

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "🔄 Updating Service: $SERVICE_NAME"
    
    ./updateDBServiceHostPort.sh "$SERVICE_NAME" "$NEW_HOST_PORT"
    
    echo "------------------------------------------"
done

echo "✅ Suite update complete."
