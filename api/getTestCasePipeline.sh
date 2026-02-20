#!/bin/bash

# 1. Validate Input
TEST_CASE_FQN=$1

if [ -z "$TEST_CASE_FQN" ]; then
    echo "❌ Usage: ./getTestCasePipeline.sh <test_case_fqn>"
    exit 1
fi

# 2. Validate Environment Variables
if [ -z "$TOKEN" ] || [ -z "$API_BASE" ]; then
    echo "❌ Error: Missing environment variables (TOKEN or API_BASE)."
    exit 1
fi

# Sanitize API_BASE
BASE_URL=$(echo "${API_BASE}" | sed 's#/$##')

echo "🔍 Fetching for the data quality test details: ${TEST_CASE_FQN}..."
#  can see data quality tests going to Observability->Data Quality->Test Cases
#  click on name
#  copy the URL and edit off the https://{{API_BASE}}/test-case
#  remove test-case-results off end of URL

# URL Encode the FQN (handling spaces and other common special characters)
ENCODED_FQN=$(echo "$TEST_CASE_FQN" | sed 's/ /%20/g; s/\[/%5B/g; s/\]/%5D/g')

# Fetch Test Case - explicitly request testSuite and testCaseResult fields
RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/dataQuality/testCases/name/${ENCODED_FQN}?fields=testSuite,testCaseResult")

# Extract Test Case Details
CASE_ID=$(echo "$RESPONSE" | jq -r '.id // empty')
CASE_STATUS=$(echo "$RESPONSE" | jq -r '.testCaseResult.testCaseStatus // "Unknown"')
CASE_RESULT_TIME=$(echo "$RESPONSE" | jq -r '.testCaseResult.timestamp // empty')

# Extract Test Suite Details
TEST_SUITE_ID=$(echo "$RESPONSE" | jq -r '.testSuite.id // empty')
TEST_SUITE_FQN=$(echo "$RESPONSE" | jq -r '.testSuite.fullyQualifiedName // empty')

# Show Data Quality Test Info
echo "------------------------------------------------"
echo "📝 DATA QUALITY TEST: ${TEST_CASE_FQN}"
echo "🆔 ID:       ${CASE_ID}"
case "$CASE_STATUS" in
    "Success") EMOJI="✅" ;;
    "Failed")  EMOJI="❌" ;;
    "Aborted") EMOJI="⚠️" ;;
    *)         EMOJI="❓" ;;
esac

# Convert timestamp if available
if [ -n "$CASE_RESULT_TIME" ] && [ "$CASE_RESULT_TIME" != "null" ]; then
    CASE_TIME_SEC=$((CASE_RESULT_TIME / 1000))
    CASE_TIME_STR=$(date -r "$CASE_TIME_SEC" "+%Y-%m-%d %H:%M:%S %Z" 2>/dev/null || echo "$CASE_RESULT_TIME")
    echo "📊 Status:   $EMOJI $CASE_STATUS (last checked: $CASE_TIME_STR)"
else
    echo "📊 Status:   $EMOJI $CASE_STATUS"
fi
echo "------------------------------------------------"

if [ -z "$TEST_SUITE_ID" ] || [ "$TEST_SUITE_ID" == "null" ]; then
    echo "❌ Error: No Test Suite ID linked in Test Case metadata."
    echo "Cannot proceed without a direct Test Suite ID."
    exit 1
fi

echo "✅ Found Test Suite: ${TEST_SUITE_FQN}"
echo "🆔 Test Suite ID:   ${TEST_SUITE_ID}"

echo ""
echo "🔍 Fetching health metadata for Test Suite..."
#  Observability->Data Quality->Test Suites

# Fetch the TestSuite entity directly using its ID ONLY
URL="${BASE_URL}/dataQuality/testSuites/${TEST_SUITE_ID}?fields=pipelines,testCaseResultSummary"
SUITE_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "$URL")

# --- PRIMARY STATUS: Test Result Summary (The "Health" of the tests) ---
echo "================================================"
echo "🩺 TEST SUITE HEALTH (Current Results)"
echo "================================================"
# testCaseResultSummary is an array of objects: {"testCaseName": "...", "status": "Success", ...}
SUCCESS=$(echo "$SUITE_RESPONSE" | jq -r '[.testCaseResultSummary[]? | select(.status == "Success")] | length')
FAILED=$(echo "$SUITE_RESPONSE" | jq -r '[.testCaseResultSummary[]? | select(.status == "Failed")] | length')
ABORTED=$(echo "$SUITE_RESPONSE" | jq -r '[.testCaseResultSummary[]? | select(.status == "Aborted")] | length')
TOTAL=$(echo "$SUITE_RESPONSE" | jq -r '(.testCaseResultSummary // []) | length')

echo "✅ Passed:  $SUCCESS"
echo "❌ Failed:  $FAILED"
echo "⚠️  Aborted: $ABORTED"
echo "📊 Total:   $TOTAL cases"

# Determine Overall Health Status
if [ "$FAILED" -gt 0 ]; then
    echo "🚨 STATUS:  FAILED"
elif [ "$TOTAL" -eq 0 ]; then
    echo "⚪ STATUS:  NO RESULTS"
else
    echo "🟢 STATUS:  HEALTHY"
fi
echo "================================================"

# --- SECONDARY INFO: Orchestration (How tests are triggered) ---
PIPELINE_IDS=$(echo "$SUITE_RESPONSE" | jq -r '.pipelines[].id // empty' 2>/dev/null)
#  Settings->Services->Data Observability->Pipelines

if [ ! -z "$PIPELINE_IDS" ] && [ "$PIPELINE_IDS" != "null" ]; then
    echo ""
    echo "⚙️  ORCHESTRATION (Ingestion Pipelines)"
    echo "💡 Note: A Test Suite can have multiple pipelines if there are multiple schedules,"
    echo "         if old pipelines were deleted (soft delete), or if manually triggered."
    echo "⚠️  State = 'failed' means the EXECUTOR (Arco) crashed or cannot connect to the source,"
    echo "   regardless of whether the data is actually healthy."
    echo "------------------------------------------------"
    
    for ID in $PIPELINE_IDS; do
        # Fetch name/type from backup in suite response first
        P_NAME=$(echo "$SUITE_RESPONSE" | jq -r --arg id "$ID" '.pipelines[] | select(.id == $id) | .name // "Unknown"')
        P_TYPE=$(echo "$SUITE_RESPONSE" | jq -r --arg id "$ID" '.pipelines[] | select(.id == $id) | .pipelineType // "Unknown"')

        # Fetch full details individually for orchestration status USING ID (with include=all to catch soft-deleted ones)
        DETAIL_RESPONSE=$(curl -s -L -H "Authorization: Bearer $TOKEN" "${BASE_URL}/services/ingestionPipelines/${ID}?fields=pipelineStatuses&include=all")
        
        # Check if the fetch succeeded
        FETCH_NAME=$(echo "$DETAIL_RESPONSE" | jq -r '.name // empty')
        FETCH_DISPLAY_NAME=$(echo "$DETAIL_RESPONSE" | jq -r '.displayName // empty')
        P_FQN=$(echo "$DETAIL_RESPONSE" | jq -r '.fullyQualifiedName // empty')
        
        if [ -z "$FETCH_NAME" ] || [ "$FETCH_NAME" == "null" ]; then
            ORCH_STATUS="⚠️  CONNECTION_ERROR (Orphaned metadata?)"
            LAST_RUN="N/A"
        else
            # Prefer displayName if available (this is what the UI shows)
            if [ -n "$FETCH_DISPLAY_NAME" ] && [ "$FETCH_DISPLAY_NAME" != "null" ]; then
                P_NAME="$FETCH_DISPLAY_NAME"
            else
                P_NAME="$FETCH_NAME"
            fi
            
            # Check if this is a soft-deleted pipeline
            IS_DELETED=$(echo "$DETAIL_RESPONSE" | jq -r '.deleted // false')
            if [ "$IS_DELETED" == "true" ]; then
                P_NAME="🗑️  [DELETED] $P_NAME"
            else
                P_NAME="🟢 [ACTIVE] $P_NAME"
            fi

            # Parse status (Arco check / last run check)
            # The field is usually `pipelineStatuses`, but might be missing entirely if it never ran
            STATUS_INFO=$(echo "$DETAIL_RESPONSE" | jq -r '.pipelineStatuses // empty')
            
            if [ "$STATUS_INFO" == "null" ] || [ -z "$STATUS_INFO" ]; then
                ORCH_STATUS="⚠️  ORCHESTRATION_ERROR (Not in Arco or Never Run)"
                LAST_RUN="N/A"
            else
                STATE=$(echo "$DETAIL_RESPONSE" | jq -r '.pipelineStatuses.pipelineState // "no_status"')
                LAST_RUN_MS=$(echo "$DETAIL_RESPONSE" | jq -r '.pipelineStatuses.endDate // empty')
                
                if [ -n "$LAST_RUN_MS" ] && [ "$LAST_RUN_MS" != "null" ]; then
                    # Convert milliseconds to seconds for date -r (Mac compatible)
                    LAST_RUN_SEC=$((LAST_RUN_MS / 1000))
                    LAST_RUN=$(date -r "$LAST_RUN_SEC" "+%Y-%m-%d %H:%M:%S %Z" 2>/dev/null || echo "$LAST_RUN_MS")
                else
                    LAST_RUN="never"
                fi
                
                case "$STATE" in
                    "success") STATUS_EMOJI="✅" ;;
                    "running") STATUS_EMOJI="⏳" ;;
                    "failed")  STATUS_EMOJI="❌" ;;
                    *)         STATUS_EMOJI="❓" ;;
                esac
                ORCH_STATUS="$STATUS_EMOJI $STATE"
            fi
        fi

        echo "🔗 Pipeline: $P_NAME ($P_TYPE)"
        echo "🆔 ID:       $ID"
        echo "📊 State:    $ORCH_STATUS"
        echo "🕒 Executed: $LAST_RUN"
        echo "------------------------------------------------"
    done
else
    echo ""
    echo "⚠️  No ingestion pipelines linked. Tests may be running via Profiler or manually."
fi
