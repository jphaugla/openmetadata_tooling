#!/bin/bash

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "------------------------------------------"
    
    # 1. Get the Service ID
    SERVICE_ID=$(curl -s -X GET "$API_BASE/services/databaseServices/name/${SERVICE_NAME}" \
      -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | grep -o '[^"]*$')

    if [ ! -z "$SERVICE_ID" ]; then
        echo "🚀 Triggering AutoPilot for $SERVICE_NAME..."
        # 2. Trigger the AutoPilot Agent
        curl -s -X POST "$API_BASE/services/databaseServices/triggerAutoPilot/$SERVICE_ID" \
        -H "Authorization: Bearer $TOKEN" -w " Status: %{http_code}\n"
    else
        echo "❌ Service $SERVICE_NAME not found."
    fi
done
