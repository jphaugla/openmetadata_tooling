#!/bin/bash

INPUT_FILE=$1

# 1. Validate Input and Environment
if [ -z "$INPUT_FILE" ] || [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: Please provide a valid JSON file."
    echo "Usage: ./importGlossary.sh <exported_glossary.json>"
    exit 1
fi

if [ -z "$TOKEN" ] || [ -z "$API_BASE" ] || [ -z "$OWNER_ID" ]; then
    echo "❌ Error: Missing environment variables (TOKEN, API_BASE, or OWNER_ID)."
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🚀 Importing Glossary from: $INPUT_FILE"
echo "👤 Assigning Owner ID: $OWNER_ID"

# 2. Extract and Import the Glossary
CLEAN_GLOSSARY=$(jq -c --arg owner_id "$OWNER_ID" '
.glossary | {
    name: .name,
    displayName: .displayName,
    description: .description,
    mutuallyExclusive: .mutuallyExclusive,
    owners: [{id: $owner_id, type: "user"}]
}' "$INPUT_FILE")

echo "📡 Sending POST request for Glossary..."
RESPONSE=$(curl -s -L -X POST "${BASE_URL}/glossaries" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$CLEAN_GLOSSARY")

NEW_GLOSSARY_ID=$(echo "$RESPONSE" | jq -r '.id // empty')
NEW_GLOSSARY_NAME=$(echo "$RESPONSE" | jq -r '.name // empty')

if [ -z "$NEW_GLOSSARY_ID" ] || [ "$NEW_GLOSSARY_ID" == "null" ]; then
    # Check if it already exists
    if echo "$RESPONSE" | grep -q "409"; then
        echo "ℹ️ Glossary already exists. Fetching existing definition..."
        GLOSSARY_NAME_TO_FETCH=$(echo "$CLEAN_GLOSSARY" | jq -r '.name')
        ENCODED_GNAME=$(echo "$GLOSSARY_NAME_TO_FETCH" | sed 's/ /%20/g')
        RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/glossaries/name/${ENCODED_GNAME}")
        NEW_GLOSSARY_ID=$(echo "$RESPONSE" | jq -r '.id // empty')
        NEW_GLOSSARY_NAME=$(echo "$RESPONSE" | jq -r '.name // empty')
    fi
fi

if [ -z "$NEW_GLOSSARY_ID" ] || [ "$NEW_GLOSSARY_ID" == "null" ]; then
    echo "❌ Failed to import glossary."
    echo "💬 Server Response: $RESPONSE"
    exit 1
fi

echo "✅ Glossary successfully resolved! ID: $NEW_GLOSSARY_ID"

# 3. Import Glossary Terms
echo "📦 Importing Glossary Terms..."

# We use two passes to handle parents: 
# Pass 1: Create all terms (top-level and children) without parent links.
# Pass 2: Update terms with parent links once all terms exist.
# However, for simplicity and typical API behavior, we will:
# 1. Sort terms by depth (if possible) or just try multiple times.
# 2. For now, let's fix the GLOSSARY and PARENT fields to use NAMEs or proper references.

jq -c '.terms[]' "$INPUT_FILE" | while read -r term; do
    TERM_NAME=$(echo "$term" | jq -r '.name')
    
    # Clean the term JSON:
    # - glossary: The target API for CreateGlossaryTerm expects the Glossary NAME
    # - parent: If exists, the target API expects the FQN or ID of the parent. 
    #   We will use the parent FQN from the source, as it should match if we import everything.
    CLEAN_TERM=$(echo "$term" | jq -c --arg gname "$NEW_GLOSSARY_NAME" --arg owner_id "$OWNER_ID" '
    {
        name: .name,
        displayName: .displayName,
        description: .description,
        glossary: $gname,
        owners: [{id: $owner_id, type: "user"}],
        synonyms: .synonyms,
        relatedTerms: .relatedTerms,
        references: .references,
        mutuallyExclusive: .mutuallyExclusive
    } + (if .parent then {parent: .parent.fullyQualifiedName} else {} end)')

    echo "  ➡️ Importing Term: $TERM_NAME"
    TERM_RESPONSE=$(curl -s -L -X POST "${BASE_URL}/glossaryTerms" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$CLEAN_TERM")
    
    TERM_ID=$(echo "$TERM_RESPONSE" | jq -r '.id // empty')
    
    if [ ! -z "$TERM_ID" ] && [ "$TERM_ID" != "null" ]; then
        echo "    ✅ Success"
    else
        echo "    ❌ Failed: $(echo "$TERM_RESPONSE" | jq -r '.message')"
    fi
done

echo "✨ Glossary import process complete."
