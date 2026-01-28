#!/bin/bash
# getServiceGlossaryMaps.sh
SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: ./getServiceGlossaryMaps.sh <service_name>"
    exit 1
fi

BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Identifying Service Type for: ${SERVICE_NAME}..."

# Try Database Service first
DB_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/databaseServices/name/${SERVICE_NAME}")
DB_SVC_ID=$(echo "$DB_SVC_RESPONSE" | jq -r '.id')

if [ "$DB_SVC_ID" != "null" ] && [ ! -z "$DB_SVC_ID" ]; then
    SERVICE_TYPE="databaseService"
    ENDPOINT="tables"
    FILTER="service"
    FIELDS="tags,columns"
    echo "✅ Found Database Service: ${SERVICE_NAME}"
else
    # Try Search Service
    SEARCH_SVC_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/searchServices/name/${SERVICE_NAME}")
    SEARCH_SVC_ID=$(echo "$SEARCH_SVC_RESPONSE" | jq -r '.id')
    
    if [ "$SEARCH_SVC_ID" != "null" ] && [ ! -z "$SEARCH_SVC_ID" ]; then
        SERVICE_TYPE="searchService"
        ENDPOINT="searchIndexes"
        FILTER="service"
        FIELDS="tags,fields"
        echo "✅ Found Search Service: ${SERVICE_NAME}"
    else
        echo "❌ Error: Service '${SERVICE_NAME}' not found as a Database or Search service."
        exit 1
    fi
fi

echo "📡 Exporting Glossary Mappings for $SERVICE_NAME ($SERVICE_TYPE)..."

# Fetch entities belonging to the service
URL="${BASE_URL}/${ENDPOINT}?${FILTER}=${SERVICE_NAME}&fields=${FIELDS}&limit=1000"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$URL")

# Check for API error
if echo "$RESPONSE" | jq -e '.code' > /dev/null 2>&1; then
    echo "❌ API Error: $(echo "$RESPONSE" | jq -r '.message')"
    exit 1
fi

# Extract FQN and tags. Handle both 'columns' (tables) and 'fields' (searchIndexes)
# Optimization: Only keep tagFQN and force secondary filter by service name to avoid API bleed-through
PROCESSED_JSON=$(echo "$RESPONSE" | jq --arg svc "$SERVICE_NAME" '.data // [] | 
    map(select(.fullyQualifiedName | startswith($svc))) |
    map({
    fqn: .fullyQualifiedName,
    serviceType: "'$SERVICE_TYPE'",
    tags: [(.tags // [])[] | {tagFQN: .tagFQN, source: .source}],
    columnTags: (
        if .columns then
            [.columns[] | {name: .name, tags: [(.tags // [])[] | {tagFQN: .tagFQN, source: .source}]} | select(.tags != [])]
        elif .fields then
            [.fields[] | {name: .name, tags: [(.tags // [])[] | {tagFQN: .tagFQN, source: .source}]} | select(.tags != [])]
        else
            []
        end
    )
}) | map(select(.tags != [] or (.columnTags | length > 0)))')

echo "$PROCESSED_JSON" > "${SERVICE_NAME}_glossary_map.json"

echo "✅ Saved mapping to ${SERVICE_NAME}_glossary_map.json"
COUNT=$(echo "$PROCESSED_JSON" | jq 'length')
echo "📊 Found $COUNT entities with tags."

# Debug: Show file size
ls -lh "${SERVICE_NAME}_glossary_map.json"
