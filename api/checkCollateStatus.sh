#!/bin/bash

# 1. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    echo "Make sure to export TOKEN and API_BASE (e.g., http://localhost:8585/api/v1)"
    exit 1
fi

# 2. Configure Sleep Interval & Retries
SLEEP_TIME=${SLEEP_SECONDS:-10}
MAX_RETRIES=${MAX_RETRIES:-30} 

# 3. Format URL
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')
STATUS_URL="${BASE_URL}/system/status"

echo "🔍 Monitoring Collate Server Status..."
echo "🌐 URL: $STATUS_URL"
echo "⏸️  Interval: $SLEEP_TIME seconds"
echo "------------------------------------------------"

# Components that MUST pass for the server to be considered functional
# We allow "migrations" to be false as it often reports missing migrations in Collate SaaS
CRITICAL_COMPONENTS='{"database":true, "searchInstance":true, "pipelineServiceClient":true, "jwks":true}'

COUNT=1
while [ $COUNT -le $MAX_RETRIES ]; do
    echo "📡 Attempt $COUNT/$MAX_RETRIES..."
    
    # Fetch status
    RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$STATUS_URL")
    
    # Check if we got a valid JSON response
    if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo "⚠️  Invalid JSON response or server connection error."
    else
        # Extract components that failed
        # We use 'in' which works for object keys
        FAILED_CRITICAL=$(echo "$RESPONSE" | jq -r --argjson critical "$CRITICAL_COMPONENTS" '
            to_entries 
            | map(select(.key | in($critical))) 
            | map(select(.value.passed == false)) 
            | map(.key) 
            | join(", ")')

        if [ -z "$FAILED_CRITICAL" ]; then
            echo "✅ Success: Collate server critical components are healthy!"
            
            # Check if migrations are actually failing, and just warn
            MIGRATION_STATUS=$(echo "$RESPONSE" | jq -r '.migrations.passed')
            if [ "$MIGRATION_STATUS" == "false" ]; then
                echo "⚠️  Note: Migrations are reporting incomplete, but continuing as critical services are up."
            fi
            
            echo "📄 Response: $RESPONSE"
            exit 0
        else
            echo "⚠️  Critical components failed: $FAILED_CRITICAL"
        fi
    fi
    
    if [ $COUNT -lt $MAX_RETRIES ]; then
        echo "⏳ Sleeping for $SLEEP_TIME seconds..."
        sleep "$SLEEP_TIME"
    fi
    ((COUNT++))
done

echo "❌ Failure: Collate server did not report healthy status after $MAX_RETRIES attempts."
exit 1
