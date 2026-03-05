# Set the Fully Qualified Name (FQN) for your rides table
# Based on your logs: Cockroach_movr.movr.public.rides
TABLE_FQN="Cockroach_movr.movr.public.rides"

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Fetching Lineage for: ${TABLE_FQN}..."

curl -s -L -X GET "${BASE_URL}/lineage/table/name/${TABLE_FQN}?upstreamDepth=1&downstreamDepth=1" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" | jq .
