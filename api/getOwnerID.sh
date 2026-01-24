#!/bin/bash

OWNER_NAME=$1

# 1. Validate Owner Name was passed
if [ -z "$OWNER_NAME" ]; then
    echo "❌ Error: No Owner Name provided."
    echo "Usage: ./getOwnerID.sh <owner_name>"
    exit 1
fi

if [[ "$OWNER_NAME" == *" "* ]]; then
    echo "❌ Error: Owner name '$OWNER_NAME' contains spaces. Spaces are not allowed."
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

echo "🔍 Searching for User: ${OWNER_NAME}..."

# 3. Correctly format the URL
# We remove trailing slashes from API_BASE if they exist to prevent //api
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
USER_URL="${BASE_URL}/users/name/${OWNER_NAME}"

# 4. Fetch the User Data
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$USER_URL")

# 5. Extract ID and User Info
# We use grep/seed to extract the UUID from the JSON response
OWNER_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)

# Instead of connection status (which users don't have), let's check if they are an Admin
IS_ADMIN=$(echo "$RESPONSE" | grep -o '"isAdmin":[^,}]*' | cut -d':' -f2)
IS_BOT=$(echo "$RESPONSE" | grep -o '"isBot":[^,}]*' | cut -d':' -f2)

if [ ! -z "$OWNER_ID" ]; then
    echo "✅ Found User: ${OWNER_NAME}"
    echo "🆔 ID: $OWNER_ID"
    echo "👑 Admin: ${IS_ADMIN:-false}"
    echo "🤖 Bot: ${IS_BOT:-false}"
else
    echo "❓ $OWNER_NAME not found via direct name lookup. Checking fallback search..."
    
    # Fallback: Search the users list (useful if name case-sensitivity is an issue)
    FALLBACK_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/users?limit=50")
    FALLBACK_ID=$(echo "$FALLBACK_RESPONSE" | grep -B 1 "\"name\":\"$OWNER_NAME\"" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)

    if [ ! -z "$FALLBACK_ID" ]; then
        echo "⚠️ Found via fallback! ID: $FALLBACK_ID"
    else
        echo "❌ User '$OWNER_NAME' could not be found. Check if the name matches exactly in the UI."
    fi
fi
