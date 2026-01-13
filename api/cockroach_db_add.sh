#!/bin/bash

# Validate all environment variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$MY_CRDB_USER" ] || [ -z "$MY_CRDB_PASS" ] || [ -z "$CA_CERT" ]; then
    echo "Error: Missing environment variables (TOKEN, API_BASE, MY_CRDB_USER, MY_CRDB_PASS, or CA_CERT)."
    exit 1
fi

databases=("intro" "kv" "bank" "movr" "startrek" "tpcc" "ycsb")

for db in "${databases[@]}"
do
    SERVICE_NAME="Cockroach_$db"
    echo "------------------------------------------"
    echo "Processing Database: $db"
    
    # Step 1: Create the Service using the exact exported structure
    echo "Step 1: Creating Service..."
    RESPONSE=$(curl -s -X POST "$API_BASE/services/databaseServices" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d @- <<EOF
{
  "name": "$SERVICE_NAME",
  "serviceType": "Cockroach",
  "connection": {
    "config": {
      "type": "Cockroach",
      "scheme": "cockroachdb+psycopg2",
      "username": "$MY_CRDB_USER",
      "authType": {
        "password": "$MY_CRDB_PASS"
      },
      "hostPort": "host.docker.internal:26257",
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
    
    # Extract UUID
    SERVICE_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*' | grep -o '[^"]*$')
    
    if [ -z "$SERVICE_ID" ]; then
        echo "❌ Failed to create service. Response: $RESPONSE"
        continue
    fi
    echo "✅ Created Service ID: $SERVICE_ID"

    echo "------------------------------------------"
done
