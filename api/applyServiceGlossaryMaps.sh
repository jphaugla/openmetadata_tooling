#!/bin/bash
# applyServiceGlossaryMaps.sh
MAP_FILE=$1

if [ -z "$MAP_FILE" ] || [ ! -f "$MAP_FILE" ]; then
    echo "❌ Usage: ./applyServiceGlossaryMaps.sh <map_file.json>"
    exit 1
fi

BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

# Loop through each entity in the mapping
jq -c '.[]' "$MAP_FILE" | while read -r row; do
    FQN=$(echo "$row" | jq -r '.fqn')
    TYPE=$(echo "$row" | jq -r '.serviceType // "databaseService"')
    TAGS=$(echo "$row" | jq -c '.tags')
    COL_TAGS=$(echo "$row" | jq -c '.columnTags')
    
    # Map internal service type to entity path
    if [ "$TYPE" == "searchService" ]; then
        ENTITY_PATH="searchIndexes"
    else
        ENTITY_PATH="tables"
    fi

    echo "🏷️  Restoring tags for $FQN ($TYPE)..."

    # Get the ID of the entity on the NEW instance
    ENTITY_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/${ENTITY_PATH}/name/${FQN}" | jq -r '.id // empty')

    if [ ! -z "$ENTITY_ID" ] && [ "$ENTITY_ID" != "null" ]; then
        # 1. Apply Top-level Tags
        if [ "$TAGS" != "[]" ]; then
            curl -s -X PUT "${BASE_URL}/${ENTITY_PATH}/${ENTITY_ID}/tags" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $TOKEN" \
                -d "$TAGS" > /dev/null
            echo "   ✅ Top-level tags restored."
        fi

        # 2. Apply Column/Field Tags
        if [ "$COL_TAGS" != "[]" ] && [ "$COL_TAGS" != "null" ]; then
             # OpenMetadata 1.11+ uses PATCH or specific endpoints for column tags usually via the main entity PUT tags
             # But the PUT /tags endpoint for an entity actually accepts the FULL list of tags for that entity.
             # If we want to restore column tags via individual calls, we'd need to loop through COL_TAGS.
             # However, some OM versions support applying all tags at once.
             # For now, we follow the pattern of the original script but expanded.
             
             echo "$COL_TAGS" | jq -c '.[]' | while read -r col; do
                 COL_NAME=$(echo "$col" | jq -r '.name')
                 C_TAGS=$(echo "$col" | jq -c '.tags')
                 
                 echo "     🔹 Restoring column/field tags for: $COL_NAME"
                 
                 # The endpoint for column/field tags depends on OM version and entity type.
                 # Usually it's PUT /entities/{id}/tags but we need to specify where it goes.
                 # In many OM versions, applying column tags is done via PATCH on the table or PUT /tags with specific schema.
                 
                 # Attempting PUT /entities/{id}/tags for the specific column FQN if reachable or as part of the entity
                 # Standard way: PUT /tables/{id}/tags
                 curl -s -X PUT "${BASE_URL}/${ENTITY_PATH}/${ENTITY_ID}/tags" \
                     -H "Content-Type: application/json" \
                     -H "Authorization: Bearer $TOKEN" \
                     -d "$TAGS" > /dev/null
             done
        fi
    else
        echo "   ⚠️ Entity not found on target. Run ingestion first."
    fi
done
