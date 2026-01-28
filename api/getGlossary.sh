#!/bin/bash

GLOSSARY_NAME=$1

# 1. Validate Input
if [ -z "$GLOSSARY_NAME" ]; then
    echo "❌ Error: No Glossary Name provided."
    echo "Usage: ./getGlossary.sh <glossary_name>"
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Checking for Glossary: ${GLOSSARY_NAME}..."

# 3. URL Encode Glossary Name for the request
ENCODED_NAME=$(echo "$GLOSSARY_NAME" | sed 's/ /%20/g')
CLEAN_URL="${BASE_URL}/glossaries/name/${ENCODED_NAME}?fields=owners,tags"

RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$CLEAN_URL")

GLOSSARY_ID=$(echo "$RESPONSE" | jq -r '.id // empty')

if [ -z "$GLOSSARY_ID" ] || [ "$GLOSSARY_ID" == "null" ]; then
    echo "❌ Glossary '$GLOSSARY_NAME' not found."
    exit 1
fi

echo "✅ Found Glossary: $GLOSSARY_NAME (ID: $GLOSSARY_ID)"

# 4. Fetch Glossary Terms
echo "📦 Fetching Glossary Terms..."
TERMS_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/glossaryTerms?glossary=${GLOSSARY_ID}&limit=1000")
TERMS_DATA=$(echo "$TERMS_RESPONSE" | jq -c '.data')

# 5. Combine and Save
FILE_NAME="${GLOSSARY_NAME// /_}_glossary.json"
echo "💾 Saving to $FILE_NAME..."

jq -n --argjson glossary "$RESPONSE" --argjson terms "$TERMS_DATA" \
'{
    glossary: $glossary,
    terms: $terms
}' > "$FILE_NAME"

echo "✨ Done! Exported to $FILE_NAME"
