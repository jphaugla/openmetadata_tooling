#!/bin/bash

# Validate all environment variables
# Ensure OWNER_ID is set in your setEnv.sh
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$MY_CRDB_USER" ] || [ -z "$MY_CRDB_PASS" ] || [ -z "$CA_CERT" ] || [ -z "$CRDB_HOST_PORT" ] || [ -z "$OWNER_ID" ]; then
    echo "Error: Missing environment variables (TOKEN, API_BASE, MY_CRDB_USER, MY_CRDB_PASS, CA_CERT, or OWNER_ID)."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "------------------------------------------"
    echo "Processing Database: $db"
    
    echo "Step 1: Creating Service with Owner..."
    RESPONSE=$(curl -s -X POST "$API_BASE/services/databaseServices" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d @- <<EOF
{
  "name": "$SERVICE_NAME",
  "serviceType": "Cockroach",
  "owners": [
    {
      "id": "$OWNER_ID",
      "type": "user"
    }
  ],
  "connection": {
    "config": {
      "type": "Cockroach",
      "scheme": "cockroachdb+psycopg2",
      "username": "$MY_CRDB_USER",
      "authType": {
        "password": "$MY_CRDB_PASS"
      },
      "hostPort": "${CRDB_HOST_PORT}",
      "database": "$db",
      "ingestAllDatabases": false,
      "databaseSchema": "public",
      "sslConfig": {
        "caCertificate": "$CA_CERT"
      },
      "sslMode": "verify-full",
      "connectionOptions": {
        "password": "$MY_CRDB_PASS"
      },
      "supportsMetadataExtraction": true,
      "supportsProfiler": true
    }
  }
}
EOF
)
    
    # Updated Extract UUID to be more specific to the service ID
    SERVICE_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*' | head -n 1 | grep -o '[^"]*$')
    
    if [ -z "$SERVICE_ID" ]; then
        echo "❌ Failed to create service. Response: $RESPONSE"
        continue
    fi
    echo "✅ Created Service ID: $SERVICE_ID"

    echo "------------------------------------------"
done
