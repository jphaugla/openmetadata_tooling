#!/bin/bash
# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

# FQNs
USERS_FQN="Cockroach_movr.movr.public.users"
RIDES_FQN="Cockroach_movr.movr.public.rides"
VIEW_FQN="Cockroach_movr.movr.public.customer_summary_view"

# 1. Get IDs for the entities
echo "🔍 Fetching Entity IDs..."

USERS_ID=$(curl -s -X GET "${BASE_URL}/tables/name/${USERS_FQN}" -H "Authorization: Bearer $TOKEN" | jq -r '.id')
RIDES_ID=$(curl -s -X GET "${BASE_URL}/tables/name/${RIDES_FQN}" -H "Authorization: Bearer $TOKEN" | jq -r '.id')
VIEW_ID=$(curl -s -X GET "${BASE_URL}/tables/name/${VIEW_FQN}" -H "Authorization: Bearer $TOKEN" | jq -r '.id')

if [[ "$USERS_ID" == "null" || "$RIDES_ID" == "null" || "$VIEW_ID" == "null" ]]; then
    echo "❌ Error: Could not find one or more entities."
    echo "Users ID: $USERS_ID"
    echo "Rides ID: $RIDES_ID"
    echo "View ID: $VIEW_ID"
    exit 1
fi

echo "✅ Found IDs:"
echo "   Users: $USERS_ID"
echo "   Rides: $RIDES_ID"
echo "   View:  $VIEW_ID"

# 2. Link Users -> View
echo "🔗 Linking Users to View..."
curl -s -X PUT "${BASE_URL}/lineage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"edge\": {
      \"fromEntity\": {\"id\": \"${USERS_ID}\", \"type\": \"table\"},
      \"toEntity\": {\"id\": \"${VIEW_ID}\", \"type\": \"table\"}
    }
  }"

# 3. Link Rides -> View
echo -e "\n🔗 Linking Rides to View..."
curl -s -X PUT "${BASE_URL}/lineage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"edge\": {
      \"fromEntity\": {\"id\": \"${RIDES_ID}\", \"type\": \"table\"},
      \"toEntity\": {\"id\": \"${VIEW_ID}\", \"type\": \"table\"}
    }
  }"

echo -e "\n✅ Lineage creation complete!"
