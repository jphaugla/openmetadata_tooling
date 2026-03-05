#!/bin/bash
mkdir -p "${JSON_DIR:-../json}"

SERVICE_NAME=$1

# 1. Validate Service Name was passed
if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Error: No Service Name provided."
    echo "Usage: ./getDBService.sh <service_name>"
    exit 1
fi

if [[ "$SERVICE_NAME" == *" "* ]]; then
    echo "❌ Error: Service name '$SERVICE_NAME' contains spaces. Spaces are not allowed."
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

echo "🔍 Checking for Service: ${SERVICE_NAME}..."

# 3. Format URL and Fetch Data
# We sanitize the API_BASE to ensure no double slashes
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
CLEAN_URL="${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}?fields=testConnectionResult,owners,tags&include=all"

RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL")

# 4. Extract ID and Connection Status
SERVICE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)
STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*' | head -n 1 | cut -d'"' -f4)

# --- SHARED EXPORT FUNCTION ---
export_service() {
    local id=$1
    local name=$2
    
    echo "💾 Exporting JSON definition for ID: ${id}..."

    # We use the SERVICE_ID for the most accurate GET request
    # Added 'owners' and 'tags' fields so your export is complete
    curl -s -L -X GET "${BASE_URL}/services/databaseServices/${id}?fields=connection,owners,tags" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" | jq . > "${JSON_DIR:-../json}/${name}.json"
    
    echo "📂 File saved as: ${name}.json"
}

if [ ! -z "$SERVICE_ID" ]; then
    # If status is empty, it means the connection hasn't been tested yet
    [ -z "$STATUS" ] && STATUS="Unknown (Not Tested)"
    
    echo "✅ Found ${SERVICE_NAME}"
    echo "🆔 ID: $SERVICE_ID"
    echo "📡 Status: $STATUS"

    export_service "$SERVICE_ID" "$SERVICE_NAME"

else
    echo "❓ $SERVICE_NAME not found via direct name lookup. Checking fallback list..."
    
    # Fallback: Search the full list
    FALLBACK_ID=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices" | grep -B 1 "\"name\":\"$SERVICE_NAME\"" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)

    if [ ! -z "$FALLBACK_ID" ]; then
        echo "⚠️ Found via fallback! ID: $FALLBACK_ID"
        export_service "$FALLBACK_ID" "$SERVICE_NAME"
    else
        echo "❌ Really could not find $SERVICE_NAME."
    fi
fi
