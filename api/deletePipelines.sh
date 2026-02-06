#!/bin/bash
SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./deletePipelines.sh <service_name>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Finding pipelines to delete for service: ${SERVICE_NAME}..."

# 1. Fetch pipelines for this service
# We fetch fields to ensure we identify them correctly, though we only need IDs
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "${BASE_URL}/services/ingestionPipelines?fields=owners&limit=100")

# 2. Filter using jq to find IDs belonging to the service
# We capture both the ID and the Name for logging
PIPELINES_TO_DELETE=$(echo "$RESPONSE" | jq --arg svc "$SERVICE_NAME" \
    '.data[] | select(.service.name == $svc) | {id: .id, name: .name}')

# Check if empty
if [ -z "$PIPELINES_TO_DELETE" ]; then
    echo "✅ No pipelines found for ${SERVICE_NAME}. Nothing to delete."
    exit 0
fi

# 3. Iterate and Destroy
echo "$PIPELINES_TO_DELETE" | jq -c '.' | while read -r item; do
    ID=$(echo "$item" | jq -r '.id')
    NAME=$(echo "$item" | jq -r '.name')
    
    echo "🗑️  Deleting Pipeline: $NAME ($ID)..."
    
    # We use hardDelete=true to ensure names can be reused immediately
    DELETE_RESPONSE=$(curl -s -X DELETE \
        -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/services/ingestionPipelines/${ID}?hardDelete=true")
        
    # Validation: 1.11 returns the entity on success, or an error message
    if echo "$DELETE_RESPONSE" | jq -e '.id' > /dev/null; then
        echo "   ✅ Deleted."
    else
        # If it returns a code/message, it likely failed
        MSG=$(echo "$DELETE_RESPONSE" | jq -r '.message')
        echo "   ❌ Failed: $MSG"
    fi
done

echo "------------------------------------------"
echo "🧹 Cleanup complete for ${SERVICE_NAME}"
