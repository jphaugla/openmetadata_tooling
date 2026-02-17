#!/bin/bash

# 1. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    echo "Make sure to export TOKEN and API_BASE (e.g., http://localhost:8585/api/v1)"
    exit 1
fi

# 2. Configure Sleep Interval & Retries
# SLEEP_SECONDS is the interval between checks
SLEEP_TIME=${SLEEP_SECONDS:-10}
# MAX_RETRIES can be used to limit the wait, defaulting to a high number for persistence
MAX_RETRIES=${MAX_RETRIES:-30} 

# 3. Format URL
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
STATUS_URL="${BASE_URL}/system/status"

echo "🔍 Monitoring OpenMetadata Server Status..."
echo "🌐 URL: $STATUS_URL"
echo "⏸️  Interval: $SLEEP_TIME seconds"
echo "------------------------------------------------"

COUNT=1
while [ $COUNT -le $MAX_RETRIES ]; do
    echo "📡 Attempt $COUNT/$MAX_RETRIES..."
    
    # Fetch status
    RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$STATUS_URL")
    
    # Check for healthy status
    # The server returns a map of components, each with a "passed" boolean.
    # We consider it healthy if there are no "passed":false entries and at least one "passed":true.
    if ! echo "$RESPONSE" | grep -q '"passed":false' && echo "$RESPONSE" | grep -q '"passed":true'; then
        echo "✅ Success: OpenMetadata server is healthy!"
        echo "📄 Response: $RESPONSE"
        exit 0
    fi
    
    echo "⚠️  Server not ready or unhealthy. Response: $RESPONSE"
    
    if [ $COUNT -lt $MAX_RETRIES ]; then
        echo "⏳ Sleeping for $SLEEP_TIME seconds..."
        sleep "$SLEEP_TIME"
    fi
    ((COUNT++))
done

echo "❌ Failure: OpenMetadata server did not report healthy status after $MAX_RETRIES attempts."
exit 1
