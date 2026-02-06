#!/bin/bash

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

# 1. Validate Environment
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

echo "🚀 Ensuring Pipeline Service exists..."

# 1.5 Check if Pipeline Service exists, if not create it
SERVICE_CHECK=$(curl -s -X GET "${BASE_URL}/services/pipelineServices/name/Cockroach_to_Postgres_CDC" \
  -H "Authorization: Bearer $TOKEN")

if [[ $(echo "$SERVICE_CHECK" | jq -r '.code // empty') == "404" ]]; then
    echo "🏗️ Creating Pipeline Service: Cockroach_to_Postgres_CDC..."
    # We create it as a CustomPipeline type
    # If CustomPipeline is not allowed, we might need a different serviceType.
    # However, for CDC, Custom is often used if it's not a standard orchestrator.
    SERVICE_CREATE=$(curl -s -X POST "${BASE_URL}/services/pipelineServices" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Cockroach_to_Postgres_CDC",
        "serviceType": "CustomPipeline",
        "connection": {
          "config": {
            "type": "CustomPipeline",
            "sourceUrl": "cockroach://localhost:26257"
          }
        },
        "owners": [
          {
            "id": "'"$OWNER_ID"'",
            "type": "user"
          }
        ]
      }')
    
    if [[ $(echo "$SERVICE_CREATE" | jq -r '.id // empty') == "null" ]]; then
        echo "❌ Failed to create Pipeline Service."
        echo "💬 Server Response: $SERVICE_CREATE"
        exit 1
    fi
    echo "✅ Pipeline Service created."
else
    echo "✅ Pipeline Service already exists."
fi

echo "🚀 Creating CDC Pipeline entity..."

# 2. Execute the Create Pipeline Request
RESPONSE=$(curl -s -X POST "${BASE_URL}/pipelines" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "movr_cdc",
    "displayName": "MovR Changefeed Sync",
    "description": "Real-time sync from CockroachDB to Postgres",
    "service": "Cockroach_to_Postgres_CDC"
  }')

# 3. Handle the Response
NEW_ID=$(echo "$RESPONSE" | jq -r '.id // empty')

if [ ! -z "$NEW_ID" ] && [ "$NEW_ID" != "null" ]; then
    echo "✅ Pipeline successfully created!"
    echo "🆔 New Pipeline ID: $NEW_ID"
    echo "🔗 Pipeline Name: $(echo "$RESPONSE" | jq -r '.name')"
else
    echo "❌ Failed to create pipeline."
    echo "💬 Server Response: $RESPONSE"
    exit 1
fi
